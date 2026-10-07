"""
NudgeBot: Canvas Integration / Discord Bot

Originally written for the CS-3203 Software Engineering class at the University of Oklahoma in Fall 2026.

Copyright 2026 Group K: Luke Sewell, Janes Le, Daniel Brown. Not open source. All rights reserved.
"""

import unittest
import asyncio
import os

from database.backend import DBHandler


class TestBackend(unittest.TestCase):
    def setUp(self):
        super().setUp()

        self.db = DBHandler("./test_database.sqlite", "./test_key")
        asyncio.run(self.db.connect())
        asyncio.run(self.db.initialize_db())

    def tearDown(self) -> None:
        super().tearDown()

        asyncio.run(self.db.close())

        os.remove("./test_database.sqlite")

    # === individual method tests below this line ===
    def test_Initialization(self):
        asyncio.run(self.db.initialize_db())

        # if the above line didn't error, then this test passes
        self.assertTrue(True)

    def test_User(self):
        # test data
        user_id = 6767
        user_name = "Test User"

        last_row = asyncio.run(self.db.create_user(user_id, user_name))

        self.assertIsNotNone(last_row)
        if last_row is not None:
            self.assertGreater(last_row, 0)

        user_exists = asyncio.run(self.db.user_exists(user_id))
        self.assertTrue(user_exists)

    def test_ApiKey(self):
        user_id = 8585
        user_name = "Test User 2"
        base_url = "https://test.canvas.com"
        token = "aoeihfpoaihefpoiahefkjnsfuhfpauehfo"

        # not really testing for this here, but may as well
        last_row = asyncio.run(self.db.create_user(user_id, user_name))

        self.assertIsNotNone(last_row)
        if last_row is not None:
            self.assertGreater(last_row, 0)

        user_exists = asyncio.run(self.db.user_exists(user_id))
        self.assertTrue(user_exists)

        # actual content for this test case
        # need this to not error, it should simply return None
        not_api_key = asyncio.run(self.db.get_api_key(user_id))
        self.assertIsNone(not_api_key)

        # this shouldn't error
        asyncio.run(self.db.add_api_key(user_id, base_url, token))

        # should match the data
        returned_token = asyncio.run(self.db.get_api_key(user_id))
        self.assertEqual(token, returned_token)
