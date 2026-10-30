import unittest
from unittest.mock import MagicMock

from bot.bot import PerformanceMonitor


class TestSendErrorAnnouncement(unittest.TestCase):
    def setUp(self):
        self.email = MagicMock()
        self.monitor = PerformanceMonitor(
            "host@example.com", self.email, alert_cooldown=600
        )

    def test_correct_email_has_details(self):
        sent = self.monitor.send_error_announcement(
            RuntimeError("Canvas timed out"), "/courses", now=0
        )

        self.assertTrue(sent)
        self.email.assert_called_once()
        to, body = self.email.call_args[0]
        self.assertEqual(to, "host@example.com")
        self.assertIn("RuntimeError", body)
        self.assertIn("/courses", body)
        self.assertIn("1970-01-01T00:00:00", body)
        self.assertIn("Canvas timed out", body)

    def test_incorrect_no_duplicate_within_cooldown(self):
        self.monitor.send_error_announcement(RuntimeError(), "/courses", now=0)
        sent = self.monitor.send_error_announcement(RuntimeError(), "/courses", now=60)

        self.assertFalse(sent)
        self.assertEqual(self.email.call_count, 1)

    def test_boundary_one_second_before_cooldown_ends(self):
        self.monitor.send_error_announcement(RuntimeError(), "/courses", now=0)
        self.monitor.send_error_announcement(RuntimeError(), "/courses", now=599)

        self.assertEqual(self.email.call_count, 1)

    def test_boundary_exactly_when_cooldown_ends(self):
        self.monitor.send_error_announcement(RuntimeError(), "/courses", now=0)
        self.monitor.send_error_announcement(RuntimeError(), "/courses", now=600)

        self.assertEqual(self.email.call_count, 2)

    def test_edge_server_down_is_logged(self):
        self.email.side_effect = ConnectionError("SMTP unreachable")

        sent = self.monitor.send_error_announcement(RuntimeError(), "/courses", now=0)

        self.assertFalse(sent)
        self.assertEqual(len(self.monitor.log), 1)
        self.assertIn("EMAIL FAILED", self.monitor.log[0])
        self.assertIn("/courses", self.monitor.log[0])

    def test_suppressed_errors_are_still_logged(self):
        self.monitor.send_error_announcement(RuntimeError(), "/courses", now=0)
        self.monitor.send_error_announcement(RuntimeError(), "/courses", now=60)

        self.assertEqual(self.monitor.error_count, 2)
        self.assertEqual(len(self.monitor.log), 2)
        self.assertIn("SUPPRESSED", self.monitor.log[1])

    def test_different_sources_alert_independently(self):
        self.monitor.send_error_announcement(RuntimeError(), "/courses", now=0)
        self.monitor.send_error_announcement(RuntimeError(), "/assignments", now=60)

        self.assertEqual(self.email.call_count, 2)

    def test_failed_email_does_not_start_cooldown(self):
        self.email.side_effect = [ConnectionError(), None]

        self.monitor.send_error_announcement(RuntimeError(), "/courses", now=0)
        sent = self.monitor.send_error_announcement(RuntimeError(), "/courses", now=60)

        self.assertTrue(sent)
        self.assertEqual(self.email.call_count, 2)


if __name__ == "__main__":
    unittest.main()
