"""Unit 1: award_poll_points for the PolltoCanvasGrade feature."""

from collections.abc import Awaitable, Callable, Mapping
from typing import Any


def check_poll(poll: Mapping[str, Any], canvas_assignment_id: Any) -> None:
    """
    Make sure a poll is ready to be graded.

    :raises ValueError: if the poll is open, the assignment ID is missing,
        or the points are not a positive number.
    """
    if not poll.get("closed"):
        raise ValueError("Poll is still open")

    if not isinstance(canvas_assignment_id, str) or not canvas_assignment_id.strip():
        raise ValueError("Missing or invalid Canvas assignment ID")

    points = poll.get("points")
    if isinstance(points, bool) or not isinstance(points, (int, float)):
        raise ValueError("Points must be numeric")
    if points <= 0:
        raise ValueError("Points must be greater than 0")


def split_responders(
    poll: Mapping[str, Any], links: Mapping[Any, Any]
) -> tuple[list[tuple[Any, Any]], list[Any]]:
    """
    Split responders into (discord_id, canvas_id) pairs and unlinked users.

    Someone who answered twice only shows up once.
    """
    linked = []
    skipped = []
    seen = set()

    for discord_id in poll.get("responders", []):
        if discord_id in seen:
            continue
        seen.add(discord_id)

        student_id = links.get(discord_id)
        if student_id:
            linked.append((discord_id, student_id))
        else:
            skipped.append(discord_id)

    return linked, skipped


def award_poll_points(
    poll: Mapping[str, Any],
    canvas_assignment_id: Any,
    links: Mapping[Any, Any],
    canvas: Any,
) -> list[Any]:
    """Post the poll's points to Canvas for every responder with a linked account.

    poll: {"closed": bool, "points": number, "responders": [discord_id, ...]}
    links: {discord_id: canvas_student_id}
    canvas: object with post_grade(student_id, assignment_id, points)

    Returns a list of Discord IDs that were skipped (no linked Canvas account).
    Raises ValueError for an open poll, a missing/invalid assignment ID,
    or non-numeric / zero / negative points. No grades are posted in that case.
    """
    check_poll(poll, canvas_assignment_id)
    linked, skipped = split_responders(poll, links)

    for _, student_id in linked:
        canvas.post_grade(student_id, canvas_assignment_id, poll["points"])

    return skipped


async def award_poll_points_async(
    poll: Mapping[str, Any],
    canvas_assignment_id: Any,
    links: Mapping[Any, Any],
    post_grade: Callable[[Any, str, float], Awaitable[None]],
) -> dict[str, list[Any]]:
    """
    Async version of award_poll_points used by the real bot.

    :return: {"awarded": [...], "skipped": [...], "failed": [...]}
        lists of Discord IDs.
    """
    check_poll(poll, canvas_assignment_id)
    linked, skipped = split_responders(poll, links)

    awarded = []
    failed = []
    for discord_id, student_id in linked:
        # one failed request shouldn't stop everyone else from getting points
        try:
            await post_grade(student_id, canvas_assignment_id, poll["points"])
            awarded.append(discord_id)
        except Exception as e:
            print(f"Failed to post grade for {discord_id}: {e}")
            failed.append(discord_id)

    return {"awarded": awarded, "skipped": skipped, "failed": failed}


async def get_links(
    discord_ids: list[Any],
    get_api_key: Callable[[Any], Awaitable[str | None]],
    get_canvas_user_id: Callable[[str], Awaitable[int]],
) -> dict[Any, int]:
    """
    Map Discord IDs to Canvas user IDs.

    Each user is looked up with their own linked token, so nobody can get
    mapped to someone else's Canvas account. Users without a working token
    are left out.
    """
    links = {}
    for discord_id in discord_ids:
        api_key = await get_api_key(discord_id)
        if not api_key:
            continue
        try:
            links[discord_id] = await get_canvas_user_id(api_key)
        except Exception as e:
            print(f"Couldn't look up Canvas user for {discord_id}: {e}")

    return links
