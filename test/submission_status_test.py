"""
NudgeBot: Canvas Integration / Discord Bot

Originally written for the CS-3203 Software Engineering class at the University of Oklahoma in Fall 2026.

Copyright 2026 Group K: Luke Sewell, Janes Le, Daniel Brown, Will Craddock, Makenzie Toma, Finn Altaf, Jordan DeJarnett. Not open source. All rights reserved. 
"""

import unittest
from datetime import datetime, timedelta, timezone

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


if __name__ == "__main__":
    unittest.main()
