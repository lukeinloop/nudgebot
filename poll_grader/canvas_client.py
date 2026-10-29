"""Canvas API calls used by the poll grader."""

from typing import Any

import httpx

CANVAS_URL = "https://canvas.ou.edu"


async def post_grade(
    api_key: str, course_id: str, assignment_id: str, student_id: Any, points: float
) -> None:
    """
    Set a student's grade on a Canvas assignment.

    The API key has to belong to a teacher or TA of the course,
    otherwise Canvas returns 403.

    :raises httpx.HTTPError: if the request fails.
    """
    url = (
        f"{CANVAS_URL}/api/v1/courses/{course_id}"
        f"/assignments/{assignment_id}/submissions/{student_id}"
    )
    headers = {"Authorization": f"Bearer {api_key}"}
    data = {"submission[posted_grade]": f"{points:g}"}

    async with httpx.AsyncClient() as http_client:
        response = await http_client.put(url, headers=headers, data=data)
        response.raise_for_status()


async def get_canvas_user_id(api_key: str) -> int:
    """
    Get the Canvas user ID that owns an API key.

    :raises httpx.HTTPError: if the request fails.
    """
    url = f"{CANVAS_URL}/api/v1/users/self"
    headers = {"Authorization": f"Bearer {api_key}"}

    async with httpx.AsyncClient() as http_client:
        response = await http_client.get(url, headers=headers)
        response.raise_for_status()
        return int(response.json()["id"])
