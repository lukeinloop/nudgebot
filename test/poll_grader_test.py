import unittest
from unittest.mock import AsyncMock

from poll_grader.poll_grader import award_poll_points, award_poll_points_async, get_links


class FakeCanvas:
    def __init__(self):
        self.grades = {}

    def post_grade(self, student_id, assignment_id, points):
        self.grades[student_id] = points


class TestPollToCanvasGrade(unittest.TestCase):
    def setUp(self):
        self.canvas = FakeCanvas()
        self.links = {"disc1": "canvas1", "disc2": "canvas2"}

    def test_participants_awarded_points(self):
        poll = {"closed": True, "points": 2, "responders": ["disc1", "disc2"]}
        award_poll_points(poll, "A1", self.links, self.canvas)
        self.assertEqual(self.canvas.grades, {"canvas1": 2, "canvas2": 2})

    def test_open_poll_posts_nothing(self):
        poll = {"closed": False, "points": 2, "responders": ["disc1"]}
        with self.assertRaises(ValueError):
            award_poll_points(poll, "A1", self.links, self.canvas)
        self.assertEqual(self.canvas.grades, {})

    def test_duplicate_responder_awarded_once(self):
        poll = {"closed": True, "points": 2, "responders": ["disc1", "disc1"]}
        award_poll_points(poll, "A1", self.links, self.canvas)
        self.assertEqual(self.canvas.grades, {"canvas1": 2})

    def test_single_participant(self):
        poll = {"closed": True, "points": 5, "responders": ["disc2"]}
        award_poll_points(poll, "A1", self.links, self.canvas)
        self.assertEqual(self.canvas.grades, {"canvas2": 5})

    def test_zero_responses_posts_nothing(self):
        poll = {"closed": True, "points": 2, "responders": []}
        award_poll_points(poll, "A1", self.links, self.canvas)
        self.assertEqual(self.canvas.grades, {})

    def test_unlinked_responder_skipped_and_reported(self):
        poll = {"closed": True, "points": 2, "responders": ["disc1", "disc9"]}
        skipped = award_poll_points(poll, "A1", self.links, self.canvas)
        self.assertEqual(self.canvas.grades, {"canvas1": 2})
        self.assertEqual(skipped, ["disc9"])

    def test_invalid_points_rejected(self):
        for bad in (0, -1, "two", None):
            poll = {"closed": True, "points": bad, "responders": ["disc1"]}
            with self.assertRaises(ValueError):
                award_poll_points(poll, "A1", self.links, self.canvas)
        self.assertEqual(self.canvas.grades, {})

    def test_missing_assignment_id_rejected(self):
        poll = {"closed": True, "points": 2, "responders": ["disc1"]}
        for bad in ("", None):
            with self.assertRaises(ValueError):
                award_poll_points(poll, bad, self.links, self.canvas)
        self.assertEqual(self.canvas.grades, {})


class TestAwardPollPointsAsync(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.links = {"disc1": "canvas1", "disc2": "canvas2"}
        self.post_grade = AsyncMock()

    async def test_awards_all_linked_responders(self):
        poll = {"closed": True, "points": 2, "responders": ["disc1", "disc2"]}
        result = await award_poll_points_async(poll, "A1", self.links, self.post_grade)
        self.assertEqual(result["awarded"], ["disc1", "disc2"])
        self.post_grade.assert_any_await("canvas1", "A1", 2)
        self.post_grade.assert_any_await("canvas2", "A1", 2)

    async def test_one_failure_does_not_stop_the_rest(self):
        # first call fails, second works
        self.post_grade.side_effect = [Exception("Canvas error"), None]
        poll = {"closed": True, "points": 2, "responders": ["disc1", "disc2"]}
        result = await award_poll_points_async(poll, "A1", self.links, self.post_grade)
        self.assertEqual(result["failed"], ["disc1"])
        self.assertEqual(result["awarded"], ["disc2"])

    async def test_unlinked_and_duplicate(self):
        poll = {"closed": True, "points": 1, "responders": ["disc1", "disc1", "disc9"]}
        result = await award_poll_points_async(poll, "A1", self.links, self.post_grade)
        self.assertEqual(result["awarded"], ["disc1"])
        self.assertEqual(result["skipped"], ["disc9"])
        self.assertEqual(self.post_grade.await_count, 1)

    async def test_invalid_poll_posts_nothing(self):
        bad_polls = [
            ({"closed": False, "points": 2, "responders": ["disc1"]}, "A1"),
            ({"closed": True, "points": 0, "responders": ["disc1"]}, "A1"),
            ({"closed": True, "points": 2, "responders": ["disc1"]}, ""),
        ]
        for poll, assignment_id in bad_polls:
            with self.assertRaises(ValueError):
                await award_poll_points_async(poll, assignment_id, self.links, self.post_grade)
        self.post_grade.assert_not_awaited()


class TestGetLinks(unittest.IsolatedAsyncioTestCase):
    async def test_only_users_with_working_tokens(self):
        tokens = {1: "token1", 2: None, 3: "bad_token"}
        canvas_ids = {"token1": 111}

        async def get_api_key(discord_id):
            return tokens[discord_id]

        async def get_canvas_user_id(token):
            if token not in canvas_ids:
                raise Exception("invalid token")
            return canvas_ids[token]

        links = await get_links([1, 2, 3], get_api_key, get_canvas_user_id)
        self.assertEqual(links, {1: 111})


if __name__ == "__main__":
    unittest.main()
