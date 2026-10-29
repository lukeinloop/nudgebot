import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from bot.bot import assignments, client


class TestAssignments(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        # Mock Discord interaction
        self.interaction = MagicMock()
        self.interaction.user.id = 123456789
        self.interaction.response.defer = AsyncMock()
        self.interaction.followup.send = AsyncMock()

        # Mock Canvas database
        self.mock_db = MagicMock()
        self.mock_db.get_api_key = AsyncMock(
            return_value="fake_canvas_token"
        )

        # Fake assignment due tomorrow
        self.due_date = (
            datetime.now(timezone.utc) + timedelta(days=1)
        ).isoformat()

        # Fake Canvas assignment data
        self.fake_events = [
            {
                "type": "assignment",
                "assignment": {
                    "name": "Homework 1",
                    "due_at": self.due_date,
                    "course_id": 101,
                    "html_url": "https://canvas.ou.edu/test1"
                }
            },
            {
                "type": "assignment",
                "assignment": {
                    "name": "Project 1",
                    "due_at": self.due_date,
                    "course_id": 102,
                    "html_url": "https://canvas.ou.edu/test2"
                }
            }
        ]

        # Fake Canvas courses
        self.fake_courses = [
            {"id": 101, "name": "Software Engineering"},
            {"id": 102, "name": "Digital Design"}
        ]

    async def run_assignments(
        self, events, courses, days=7, course=None
    ):
        # Mock upcoming assignments response
        mock_events_response = MagicMock()
        mock_events_response.json.return_value = events

        # Mock active courses response
        mock_courses_response = MagicMock()
        mock_courses_response.json.return_value = courses

        # Mock HTTP client
        mock_http = AsyncMock()
        mock_http.get.side_effect = [
            mock_events_response,
            mock_courses_response
        ]

        # Mock async context manager
        mock_http_context = MagicMock()
        mock_http_context.__aenter__ = AsyncMock(
            return_value=mock_http
        )
        mock_http_context.__aexit__ = AsyncMock(
            return_value=None
        )

        # Run the actual assignments command
        with patch.object(
            client, "db", self.mock_db, create=True
        ), patch(
            "bot.bot.httpx.AsyncClient",
            return_value=mock_http_context
        ):
            await assignments.callback(
                self.interaction,
                days=days,
                course=course
            )

        return mock_http

    # Test 1: Valid assignment retrieval
    async def test_get_assignments(self):
        mock_http = await self.run_assignments(
            self.fake_events,
            self.fake_courses
        )

        # Verify both Canvas API calls
        self.assertEqual(mock_http.get.await_count, 2)

        # Verify assignment names are displayed
        self.interaction.followup.send.assert_awaited_once()
        message = (
            self.interaction.followup.send.await_args.args[0]
        )

        self.assertIn("Homework 1", message)
        self.assertIn("Project 1", message)
        self.assertIn("Software Engineering", message)
        self.assertIn("Digital Design", message)

    # Test 2: No upcoming assignments
    async def test_no_assignments(self):
        await self.run_assignments(
            [],
            self.fake_courses
        )

        self.interaction.followup.send.assert_awaited_once_with(
            "No assignments due in the next 7 days.",
            ephemeral=True
        )

    # Test 3: Filter assignments by course
    async def test_course_filter(self):
        await self.run_assignments(
            self.fake_events,
            self.fake_courses,
            course="Software Engineering"
        )

        message = (
            self.interaction.followup.send.await_args.args[0]
        )

        # Only Software Engineering assignments
        self.assertIn("Homework 1", message)
        self.assertIn("Software Engineering", message)
        self.assertNotIn("Project 1", message)
        self.assertNotIn("Digital Design", message)

    # Test 4: User without linked Canvas
    async def test_unlinked_user(self):
        self.mock_db.get_api_key = AsyncMock(
            return_value=None
        )

        with patch.object(
            client, "db", self.mock_db, create=True
        ):
            await assignments.callback(
                self.interaction,
                days=7,
                course=None
            )

        self.interaction.followup.send.assert_awaited_once_with(
            "You haven't linked your Canvas account yet. "
            "Use /link to get started.",
            ephemeral=True
        )


if __name__ == "__main__":
    unittest.main()
