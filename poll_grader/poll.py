"""Timed poll used by the /poll command."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

MAX_MINUTES = 120


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Poll:
    question: str
    points: float
    course_id: str
    assignment_id: str
    closes_at: datetime
    responders: list[Any] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        question: str,
        minutes: float,
        points: float,
        course_id: str,
        assignment_id: str,
        now: datetime | None = None,
    ) -> "Poll":
        """
        Start a poll that closes after the given number of minutes.

        :raises ValueError: if any of the inputs are invalid.
        """
        if not question.strip():
            raise ValueError("Question can't be empty")
        if not course_id.strip() or not assignment_id.strip():
            raise ValueError("Course ID and assignment ID are required")
        if isinstance(minutes, bool) or not isinstance(minutes, (int, float)):
            raise ValueError("Minutes must be a number")
        if not 0 < minutes <= MAX_MINUTES:
            raise ValueError(f"Minutes must be between 1 and {MAX_MINUTES}")
        if isinstance(points, bool) or not isinstance(points, (int, float)):
            raise ValueError("Points must be a number")
        if points <= 0:
            raise ValueError("Points must be greater than 0")

        start = now or now_utc()
        return cls(
            question=question.strip(),
            points=points,
            course_id=course_id.strip(),
            assignment_id=assignment_id.strip(),
            closes_at=start + timedelta(minutes=minutes),
        )

    # "now" can be passed in so the tests don't have to actually wait
    def is_closed(self, now: datetime | None = None) -> bool:
        return (now or now_utc()) >= self.closes_at

    def seconds_left(self, now: datetime | None = None) -> float:
        return max(0.0, (self.closes_at - (now or now_utc())).total_seconds())

    def add_response(self, discord_id: Any, now: datetime | None = None) -> str:
        """
        Record that a user participated.

        :return: "recorded", "duplicate", or "closed".
        """
        if self.is_closed(now):
            return "closed"
        if discord_id in self.responders:
            return "duplicate"
        self.responders.append(discord_id)
        return "recorded"

    def to_dict(self, now: datetime | None = None) -> dict[str, Any]:
        """Convert to the format award_poll_points expects."""
        return {
            "closed": self.is_closed(now),
            "points": self.points,
            "responders": list(self.responders),
        }
