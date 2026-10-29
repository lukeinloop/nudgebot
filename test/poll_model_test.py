import unittest
from datetime import datetime, timedelta, timezone

from poll_grader.poll import Poll

START = datetime(2026, 10, 30, 12, 0, tzinfo=timezone.utc)


def make_poll(minutes=10, points=2):
    return Poll.create("Pick one", minutes, points, "123", "456", now=START)


class TestPollCreate(unittest.TestCase):
    def test_closes_after_minutes(self):
        poll = make_poll(minutes=10)
        self.assertEqual(poll.closes_at, START + timedelta(minutes=10))

    def test_bad_inputs_rejected(self):
        bad_inputs = [
            ("  ", 5, 1, "1", "2"),  # empty question
            ("q", 0, 1, "1", "2"),  # zero minutes
            ("q", 500, 1, "1", "2"),  # too long
            ("q", 5, 0, "1", "2"),  # zero points
            ("q", 5, -1, "1", "2"),  # negative points
            ("q", 5, "two", "1", "2"),  # points not a number
            ("q", 5, 1, "", "2"),  # missing course
            ("q", 5, 1, "1", " "),  # missing assignment
        ]
        for args in bad_inputs:
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    Poll.create(*args, now=START)


class TestPollTiming(unittest.TestCase):
    def test_closes_exactly_at_deadline(self):
        poll = make_poll(minutes=10)
        self.assertFalse(poll.is_closed(START + timedelta(minutes=9, seconds=59)))
        self.assertTrue(poll.is_closed(START + timedelta(minutes=10)))

    def test_seconds_left(self):
        poll = make_poll(minutes=1)
        self.assertEqual(poll.seconds_left(START), 60)
        self.assertEqual(poll.seconds_left(START + timedelta(hours=1)), 0)


class TestPollResponses(unittest.TestCase):
    def test_each_user_counted_once(self):
        poll = make_poll()
        self.assertEqual(poll.add_response(1, START), "recorded")
        self.assertEqual(poll.add_response(1, START), "duplicate")
        self.assertEqual(poll.add_response(2, START), "recorded")
        self.assertEqual(poll.responders, [1, 2])

    def test_late_response_ignored(self):
        poll = make_poll(minutes=1)
        self.assertEqual(poll.add_response(1, START + timedelta(minutes=2)), "closed")
        self.assertEqual(poll.responders, [])

    def test_to_dict(self):
        poll = make_poll(minutes=1, points=3)
        poll.add_response(7, START)
        self.assertEqual(poll.to_dict(START), {"closed": False, "points": 3, "responders": [7]})
        self.assertTrue(poll.to_dict(START + timedelta(minutes=5))["closed"])


if __name__ == "__main__":
    unittest.main()
