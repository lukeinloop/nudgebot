import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from bot.bot import client, submissions
from canvas.assignments import submission_status


class TestSubmissionStatus(unittest.TestCase):
    def setUp(self):
        self.deadline = datetime.now(timezone.utc)

    def test_valid_submitted(self):
        assignment = {
            "due": self.deadline,
            "submitted_at": self.deadline - timedelta(hours=2),
        }
        self.assertEqual(submission_status(assignment), "submitted")

    def test_valid_not_submitted(self):
        assignment = {"due": self.deadline, "submitted_at": None}
        self.assertEqual(submission_status(assignment), "not_submitted")

    def test_invalid_null_assignment(self):
        with self.assertRaises(ValueError):
            submission_status(None)

    def test_invalid_missing_fields(self):
        with self.assertRaises(ValueError):
            submission_status({"due": self.deadline})

    def test_boundary_exactly_at_deadline(self):
        assignment = {"due": self.deadline, "submitted_at": self.deadline}
        self.assertEqual(submission_status(assignment), "submitted")

    def test_edge_just_after_deadline(self):
        assignment = {
            "due": self.deadline,
            "submitted_at": self.deadline + timedelta(seconds=1),
        }
        self.assertEqual(submission_status(assignment), "late")


class TestSubmissionsCommand(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        # Mock Discord interaction
        self.interaction = MagicMock()
        self.interaction.user.id = 123456789
        self.interaction.response.defer = AsyncMock()
        self.interaction.followup.send = AsyncMock()

        # Mock database with a linked Canvas account
        self.mock_db = MagicMock()
        self.mock_db.get_api_key = AsyncMock(
            return_value="fake_canvas_token"
        )

        # Reference times, relative to now so the tests never expire
        self.now = datetime.now(timezone.utc)
        self.tomorrow = self.now + timedelta(days=1)
        self.yesterday = self.now - timedelta(days=1)

        # Fake Canvas courses
        self.fake_courses = [
            {"id": 101, "name": "Software Engineering"},
            {"id": 102, "name": "Digital Design"}
        ]

    def make_assignment(self, name, due_at, submitted_at=None):
        # Create a Canvas assignment for testing
        # This has to mimic an assignment fetched with include[]=submission
        return {
            "name": name,
            "due_at": due_at.isoformat(),
            "html_url": "https://canvas.ou.edu/test",
            "submission": {
                "submitted_at": (
                    submitted_at.isoformat()
                    if submitted_at is not None
                    else None
                )
            }
        }

    async def run_submissions(
        self, assignments_by_course, days=7, course=None, api_error=None
    ):
        # Mock active courses response
        mock_courses_response = MagicMock()
        mock_courses_response.json.return_value = self.fake_courses

        if api_error is not None:
            request = httpx.Request(
                "GET", "https://canvas.ou.edu/api/v1/courses"
            )
            response = httpx.Response(
                api_error, request=request
            )
            mock_courses_response.raise_for_status.side_effect = (
                httpx.HTTPStatusError(
                    "Canvas API error",
                    request=request,
                    response=response
                )
            )

        # Mock one assignments response for each course that is fetched
        mock_assignments_responses = []
        for assignments in assignments_by_course:
            mock_assignments_response = MagicMock()
            mock_assignments_response.json.return_value = assignments
            mock_assignments_responses.append(mock_assignments_response)

        # Mock HTTP client
        mock_http = AsyncMock()
        mock_http.get.side_effect = [
            mock_courses_response,
            *mock_assignments_responses
        ]

        # Mock async context manager
        mock_http_context = MagicMock()
        mock_http_context.__aenter__ = AsyncMock(
            return_value=mock_http
        )
        mock_http_context.__aexit__ = AsyncMock(
            return_value=None
        )

        # Run the actual submissions command
        with patch.object(
            client, "db", self.mock_db, create=True
        ), patch(
            "bot.bot.httpx.AsyncClient",
            return_value=mock_http_context
        ):
            await submissions.callback(
                self.interaction,
                days=days,
                course=course
            )

        return mock_http

    # Test 1: Valid submission retrieval with every status
    async def test_get_submissions(self):
        mock_http = await self.run_submissions(
            [
                [
                    self.make_assignment(
                        "Homework 1",
                        self.tomorrow,
                        submitted_at=self.now - timedelta(hours=2)
                    ),
                    self.make_assignment(
                        "Homework 2",
                        self.now - timedelta(days=2),
                        submitted_at=self.yesterday
                    ),
                    self.make_assignment("Homework 3", self.yesterday)
                ],
                [self.make_assignment("Project 1", self.tomorrow)]
            ]
        )

        # Verify the courses call plus one assignments call per course
        self.assertEqual(mock_http.get.await_count, 3)

        # Verify assignment names and courses are displayed
        self.interaction.followup.send.assert_awaited_once()
        message = (
            self.interaction.followup.send.await_args.args[0]
        )

        self.assertIn("Homework 1", message)
        self.assertIn("Homework 2", message)
        self.assertIn("Homework 3", message)
        self.assertIn("Project 1", message)
        self.assertIn("Software Engineering", message)
        self.assertIn("Digital Design", message)

        # Verify each assignment gets the right status
        expected_statuses = {
            "Homework 1": "Submitted",
            "Homework 2": "Submitted late",
            "Homework 3": "Missing (past due)",
            "Project 1": "Not submitted yet"
        }

        for name, status in expected_statuses.items():
            block = next(
                block for block in message.split("\n\n") if name in block
            )
            self.assertIn(f"Status: **{status}**", block)

    # Test 2: Filter submissions by course
    async def test_course_filter(self):
        mock_http = await self.run_submissions(
            [[self.make_assignment("Homework 1", self.tomorrow)]],
            course="Software Engineering"
        )

        # Only the courses call and the matching course are requested
        self.assertEqual(mock_http.get.await_count, 2)

        message = (
            self.interaction.followup.send.await_args.args[0]
        )

        # Only Software Engineering assignments
        self.assertIn("Homework 1", message)
        self.assertIn("Software Engineering", message)
        self.assertNotIn("Digital Design", message)

    # Test 3: Boundary - Assignments outside the date range
    async def test_assignment_outside_date_range(self):
        await self.run_submissions(
            [
                [
                    self.make_assignment(
                        "Future Homework",
                        self.now + timedelta(days=30)
                    ),
                    self.make_assignment(
                        "Old Homework",
                        self.now - timedelta(days=30)
                    )
                ],
                []
            ],
            days=7
        )

        self.interaction.followup.send.assert_awaited_once_with(
            "No assignments due within 7 days of today.",
            ephemeral=True
        )

    # Test 4: Edge - Canvas returns no submission object
    async def test_missing_submission(self):
        assignment = self.make_assignment("Homework 1", self.tomorrow)
        assignment["submission"] = None

        await self.run_submissions([[assignment], []])

        message = (
            self.interaction.followup.send.await_args.args[0]
        )

        self.assertIn("Homework 1", message)
        self.assertIn("Status: **Not submitted yet**", message)

    # Test 5: User without linked Canvas
    async def test_unlinked_user(self):
        self.mock_db.get_api_key = AsyncMock(
            return_value=None
        )

        with patch.object(
            client, "db", self.mock_db, create=True
        ):
            await submissions.callback(
                self.interaction,
                days=7,
                course=None
            )

        self.interaction.followup.send.assert_awaited_once_with(
            "You haven't linked your Canvas account yet. "
            "Use /link to get started.",
            ephemeral=True
        )

    # Test 6: Canvas API returns an error
    async def test_canvas_api_error(self):
        await self.run_submissions(
            [],
            api_error=401
        )

        self.interaction.followup.send.assert_awaited_once_with(
            "Failed to retrieve submissions. "
            "Canvas API returned error status: 401",
            ephemeral=True
        )


if __name__ == "__main__":
    unittest.main()
