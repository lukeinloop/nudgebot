"""
NudgeBot: Canvas Integration / Discord Bot

Submission status helper: classifies an assignment as submitted, late, or not submitted.
"""

from datetime import datetime
from typing import Any, Mapping


def submission_status(assignment: Mapping[str, Any] | None) -> str:
    """Return "submitted", "late", or "not_submitted" for an assignment.

    The assignment is a mapping with:
        "due":          timezone-aware datetime of the deadline
        "submitted_at": timezone-aware datetime of the submission, or None

    A submission exactly at the deadline counts as on time. Raises ValueError for
    a missing/invalid assignment or malformed datetimes.
    """
    if assignment is None or not isinstance(assignment, Mapping):
        raise ValueError("assignment must be a mapping, got %r" % (assignment,))

    if "due" not in assignment or "submitted_at" not in assignment:
        raise ValueError("assignment must contain 'due' and 'submitted_at'")

    due = assignment["due"]
    submitted_at = assignment["submitted_at"]

    if not isinstance(due, datetime):
        raise ValueError("'due' must be a datetime")

    if submitted_at is None:
        return "not_submitted"

    if not isinstance(submitted_at, datetime):
        raise ValueError("'submitted_at' must be a datetime or None")

    if (due.tzinfo is None) != (submitted_at.tzinfo is None):
        raise ValueError("'due' and 'submitted_at' must both be timezone-aware or both naive")

    return "submitted" if submitted_at <= due else "late"
