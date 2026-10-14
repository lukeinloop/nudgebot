"""
NudgeBot: Canvas Integration / Discord Bot

Originally written for the CS-3203 Software Engineering class at the University of Oklahoma in Fall 2026.

Copyright 2026 Group K: Luke Sewell, Janes Le, Daniel Brown, Will Craddock, Makenzie Toma, Finn Altaf, Jordan DeJarnett. Not open source. All rights reserved.
"""

from collections.abc import Mapping
from datetime import datetime
from typing import Any


def submission_status(assignment: Mapping[str, Any] | None) -> str:
    """
    Get the submission status of an assignment.

    A submission made exactly at the deadline counts as on time.

    :param assignment: A dict with a "due" datetime and a "submitted_at" datetime (None if nothing was submitted).
    :type assignment: Mapping[str, Any] | None
    :raises ValueError: If the assignment is None or missing/has invalid dates.
    :return: "submitted", "late", or "not_submitted".
    :rtype: str
    """
    if not isinstance(assignment, Mapping):
        raise ValueError("assignment must be a dict with 'due' and 'submitted_at'")

    if "due" not in assignment or "submitted_at" not in assignment:
        raise ValueError("assignment is missing 'due' or 'submitted_at'")

    due = assignment["due"]
    submitted_at = assignment["submitted_at"]

    if not isinstance(due, datetime):
        raise ValueError("'due' must be a datetime")

    if submitted_at is None:
        return "not_submitted"

    if not isinstance(submitted_at, datetime):
        raise ValueError("'submitted_at' must be a datetime or None")

    # comparing aware and naive datetimes raises a TypeError, so catch it here
    if (due.tzinfo is None) != (submitted_at.tzinfo is None):
        raise ValueError("'due' and 'submitted_at' must both have a timezone or both not")

    if submitted_at <= due:
        return "submitted"
    return "late"
