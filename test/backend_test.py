import unittest

from database.backend import DBHandler


class TestBackend(unittest.TestCase):
    def setUp(self):
        super().setUp()

        self.db = DBHandler("./database.sqlite")

    # === individual method tests below this line ===
