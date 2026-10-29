import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from bot.bot import courses, client

class TestCourses(unittest.IsolatedAsyncioTestCase):

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

        # Fake Canvas courses
        self.fake_courses = [
            {
                "id": 101,
                "name": "Software Engineering"
            },
            {
                "id": 102,
                "name": "bruh"
            }
        ]

    async def run_courses(self, course_data, api_error=None):
        # Mock the Canvas API response
        mock_response = MagicMock()
        mock_response.json.return_value = course_data

        if api_error is not None:
            request = httpx.Request(
                "GET", "https://canvas.ou.edu/api/v1/courses"
            )
            response = httpx.Response(
                api_error, request=request
            )
            mock_response.raise_for_status.side_effect = (
                httpx.HTTPStatusError(
                    "Canvas API error",
                    request=request,
                    response=response
                )
            )

        # Mock the HTTP client
        mock_http = AsyncMock()
        mock_http.get.return_value = mock_response

        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(
            return_value=mock_http
        )
        mock_context.__aexit__ = AsyncMock(
            return_value=None
        )

        # Run the actual /courses command
        with patch.object(
            client, "db", self.mock_db, create=True
        ), patch(
            "bot.bot.httpx.AsyncClient",
            return_value=mock_context
        ):
            await courses.callback(self.interaction)

        return mock_http

    # Test 1: Successfully retrieve courses
    async def test_get_courses(self):
        mock_http = await self.run_courses(
            self.fake_courses
        )

        # Verify Canvas API was called
        mock_http.get.assert_awaited_once_with(
            "https://canvas.ou.edu/api/v1/courses",
            headers={
                "Authorization": "Bearer fake_canvas_token"
            },
            params={
                "per_page": 20,
                "enrollment_state": "active"
            }
        )

        # Verify both courses are displayed
        self.interaction.followup.send.assert_awaited_once()

        message = (
            self.interaction.followup.send.await_args.args[0]
        )

        self.assertIn("Software Engineering", message)
        self.assertIn("bruh", message)
        self.assertIn("101", message)
        self.assertIn("102", message)

    # Test 2: No active courses
    async def test_no_courses(self):
        await self.run_courses([])

        self.interaction.followup.send.assert_awaited_once_with(
            "No active courses found.",
            ephemeral=True
        )

    # Test 3: User has not linked Canvas
    async def test_unlinked_user(self):
        self.mock_db.get_api_key = AsyncMock(
            return_value=None
        )

        with patch.object(
            client, "db", self.mock_db, create=True
        ):
            await courses.callback(self.interaction)

        self.interaction.followup.send.assert_awaited_once_with(
            "You haven't linked your Canvas account yet. "
            "Use /link to get started.",
            ephemeral=True
        )

    # Test 4: Canvas API returns an error
    async def test_canvas_api_error(self):
        await self.run_courses(
            [],
            api_error=401
        )

        self.interaction.followup.send.assert_awaited_once_with(
            "Failed to retrieve courses. "
            "Canvas API returned error status: 401",
            ephemeral=True
        )


if __name__ == "__main__":
    unittest.main()
