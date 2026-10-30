import unittest
from datetime import datetime, timedelta, timezone

from bot.bot import createPriorityList

# Reference time so tests remain consistent 
NOW = datetime(2026, 10, 13, tzinfo=timezone.utc)

class TestAssignmentPriority(unittest.TestCase):
    def setUp(self):
        # Set up reusable course mappings and test assignments

        self.course_names = {
            101: "Software Engineering",
            102: "Statistics",
            103: "Theory of Computation",
            104: "Intro to OS",
        }

    def make_event(self, name, course_id, due_at, points_possible=100, submitted=False):
        # Create a Canvas assignment event for testing
        # This has to mimic the layout of the assignments imported from Canvas
        # so that's why there's so much extra stuff
        return {
            "type": "assignment",
            "assignment": {
                "name": name,
                "course_id": course_id,
                "due_at": (
                    due_at.isoformat().replace("+00:00", "Z")
                    if due_at is not None
                    else None
                ),
                "points_possible": points_possible,
                "has_submitted_submissions": submitted,
                "html_url": f"https://canvas.thisistheunittest.com/assignments/{name}",
            },
        }
    # Test 1: A normal run with correct inputs
    def test_create_priority_list(self):
        # Assignments should be sorted by calculated priority 

        # Create the assignments for testing
        assignments = [
            self.make_event(
                "Assignment 3",
                101,
                NOW + timedelta(days=3),
                points_possible=100
            ),
            self.make_event(
                "Quiz 6",
                102,
                NOW + timedelta(days=1),
                points_possible=20
            ),
            self.make_event(
                "Homework 4",
                103,
                NOW + timedelta(days=1),
                points_possible=100
            ),
        ]

        # Call the function with the above assignments
        result = createPriorityList(assignments, days=7, now=NOW, course_names=self.course_names)

        # We grab the ordered list of just the names
        actual_order = [assignment["name"] for assignment in result]

        # What we expecct 
        # Homework 4 should have a score of 50 (Closer due date than assignment 3)
        # Assignment 3 should have 40
        # and Quiz 6 will have a score of 20
        expected_order = [
            "Homework 4",
            "Assignment 3",
            "Quiz 6",
        ]

        self.assertEqual(actual_order, expected_order)

    # Test 2: No input
    def test_empty_assignment_list(self):
        result = createPriorityList([], now=NOW, course_names=self.course_names)

        self.assertEqual(result, [])

    # Test 3: A single assignment
    def test_boundary_single_assignment(self):
        assignment = self.make_event(
            "Project 3",
            104,
            NOW + timedelta(days=7),
            points_possible=150
        )

        result = createPriorityList([assignment], days=7, now=NOW, course_names=self.course_names)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Project 3")
        self.assertEqual(result[0]["course"], "Intro to OS")

   # Test 4: Assignment that is outside the given date range
    def test_assignment_outside_date_range(self):
        # Assignments due after the requested window should be excluded.

        assignment = self.make_event(
            "Final Project",
            101,
            NOW + timedelta(days=8),
        )

        result = createPriorityList(
            [assignment],
            days=7,
            now=NOW,
            course_names=self.course_names,
        )

        self.assertEqual(result, [])


    # Test 5: Assignment without a due date
    def test_edge_missing_deadline(self):
        # Assignments without due dates should be excluded
        assignments = [
            self.make_event(
                "Feedback Form",
                101,
                None,
                points_possible=10,
            ),
            self.make_event(
                "Quiz 3",
                102,
                NOW + timedelta(days=1),
                points_possible=50,
            ),
        ]

        result = createPriorityList(assignments, now=NOW, course_names=self.course_names)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Quiz 3")

if __name__ == "__main__":
    unittest.main()