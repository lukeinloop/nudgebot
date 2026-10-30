import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from poll_grader.canvas_client import get_canvas_user_id, post_grade


def mock_http_client(response):
    """Fake httpx.AsyncClient that returns the given response."""
    mock_http = AsyncMock()
    mock_http.put.return_value = response
    mock_http.get.return_value = response

    mock_context = MagicMock()
    mock_context.__aenter__ = AsyncMock(return_value=mock_http)
    mock_context.__aexit__ = AsyncMock(return_value=None)
    return mock_http, mock_context


def error_response(status):
    """Fake response whose raise_for_status raises like a real Canvas error."""
    request = httpx.Request("PUT", "https://canvas.ou.edu")
    response = MagicMock()
    response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Canvas API error", request=request, response=httpx.Response(status, request=request)
    )
    return response


class TestPostGrade(unittest.IsolatedAsyncioTestCase):
    async def test_sends_correct_request(self):
        mock_http, mock_context = mock_http_client(MagicMock())

        with patch("poll_grader.canvas_client.httpx.AsyncClient", return_value=mock_context):
            await post_grade("fake_token", "123", "456", 999, 2.5)

        mock_http.put.assert_awaited_once_with(
            "https://canvas.ou.edu/api/v1/courses/123/assignments/456/submissions/999",
            headers={"Authorization": "Bearer fake_token"},
            data={"submission[posted_grade]": "2.5"},
        )

    async def test_whole_number_points(self):
        mock_http, mock_context = mock_http_client(MagicMock())

        with patch("poll_grader.canvas_client.httpx.AsyncClient", return_value=mock_context):
            await post_grade("fake_token", "123", "456", 999, 2.0)

        self.assertEqual(mock_http.put.call_args.kwargs["data"], {"submission[posted_grade]": "2"})

    async def test_canvas_error_raises(self):
        _, mock_context = mock_http_client(error_response(403))

        with patch("poll_grader.canvas_client.httpx.AsyncClient", return_value=mock_context):
            with self.assertRaises(httpx.HTTPStatusError):
                await post_grade("student_token", "123", "456", 999, 2)


class TestGetCanvasUserId(unittest.IsolatedAsyncioTestCase):
    async def test_returns_id(self):
        response = MagicMock()
        response.json.return_value = {"id": 321, "name": "Test Student"}
        mock_http, mock_context = mock_http_client(response)

        with patch("poll_grader.canvas_client.httpx.AsyncClient", return_value=mock_context):
            self.assertEqual(await get_canvas_user_id("fake_token"), 321)

        mock_http.get.assert_awaited_once_with(
            "https://canvas.ou.edu/api/v1/users/self",
            headers={"Authorization": "Bearer fake_token"},
        )

    async def test_bad_token_raises(self):
        _, mock_context = mock_http_client(error_response(401))

        with patch("poll_grader.canvas_client.httpx.AsyncClient", return_value=mock_context):
            with self.assertRaises(httpx.HTTPStatusError):
                await get_canvas_user_id("bad_token")


if __name__ == "__main__":
    unittest.main()
