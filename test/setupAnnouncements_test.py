"""
NudgeBot: Canvas Integration / Discord Bot

Originally written for the CS-3203 Software Engineering class at the University of Oklahoma in Fall 2026.

Copyright 2026 Group K: Luke Sewell, Janes Le, Daniel Brown. Not open source. All rights reserved.
"""

from pathlib import Path
import unittest
import asyncio
from unittest.mock import MagicMock, patch

import discord
from database.backend import DBHandler
from bot.bot import intents, NudgeBot, setup_announcements


DB_PATH = "./test_database.sqlite"
DEBUG = False


# also patch the client object in the bot, because obviously it's uninitialized as we don't directly import the module,
# we only care about the setup_announcements function.
# patch.object(bot.bot, "client", autospec=NudgeBot, create=True).start()  # type: ignore
# bot.bot.client.user = MagicMock(autospec=discord.User)
# bot.bot.client.user.id = 123456789

class TestSetupAnnouncements(unittest.TestCase):
    def setUp(self):
        super().setUp()

        # delete old test DB if it is still there
        Path(DB_PATH).unlink(missing_ok=True)

        self.db = DBHandler(DB_PATH, "./test_key.key")
        asyncio.run(self.db.connect())
        asyncio.run(self.db.initialize_db())

        #TODO what's the point of making a separate DB handler if we're just going to use the real one anyways?
        # bot.bot.client.db = self.db

        # ensure all following INFO prints are on good lines
        if DEBUG:
            print()

        # I did a lot of work and research in trying to create real (not mocked) objects for all of these,
        # to ensure that it would actually be a useful unit test, but unfortunately the library is just not set up for that.
        # if it looks more doable in the future, or somebody has time, look back in the commit history for this file,
        # specifically on the feat/canvas-announcements branch, to get an idea of how you might be able to do it.

        #TODO still need data payloads and everything
        self.fake_discord_server = MagicMock(discord.Guild, autospec=True)

        # discord server that the bot is not in
        self.evil_discord_server = MagicMock(discord.Guild, autospec=True)

        # fake discord channel(s)
        self.fake_discord_channels = {
            0: MagicMock(discord.TextChannel, autospec=True),
            1: MagicMock(discord.TextChannel, autospec=True),
            2: MagicMock(discord.TextChannel, autospec=True),
            3: MagicMock(discord.TextChannel, autospec=True),
            4: MagicMock(discord.TextChannel, autospec=True),
        }

        # fake discord users
        self.fake_discord_users = {
            0: MagicMock(discord.User, autospec=True),
            1: MagicMock(discord.User, autospec=True),
            2: MagicMock(discord.User, autospec=True),
            3: MagicMock(discord.User, autospec=True),
            4: MagicMock(discord.User, autospec=True),
            5: MagicMock(discord.User, autospec=True),
        }

        # make fake interactions
        self.interaction = MagicMock(discord.Interaction, autospec=True)

        # fake canvas data
        self.fake_access_tokens = [
            "fake_token_1",
            "48749864164898146514w6ef496sef469asf",
            "85as4f+6asf46e41f65asf",
            "bot_access_token-apihfp9ahefienfon"
        ]

        # ========= set up the test database with fake data =========
        # create fake users
        count = 0
        self.fake_user_ids = [] # internal DB IDs
        for id, fake_discord_user in self.fake_discord_users.items():
            internal_id = asyncio.run(
                self.db.create_user(fake_discord_user.id, fake_discord_user.name)
            )

            self.fake_user_ids.append(internal_id)

            # give them API tokens
            ret = asyncio.run(
                self.db.add_api_key(
                    fake_discord_user.id,
                    "https://canvas.ou.edu/",
                    self.fake_access_tokens[id],
                )
            )

        # create fake classes (as the enrollments table has a foreign key from the courses table)
        self.fake_courses = [
            {
                "course_id": 824691,
                "name": "Example Class 1",
                "code": "EX-2923",
                "term": 34,
            },
            {
                "course_id": 130058,
                "name": "Example Class 2",
                "code": "ECE-2032",
                "term": 35,
            },
            {
                "course_id": 116842,
                "name": "Evil Class Eight",
                "code": "CS-3203",
                "term": 31,
            },
            {
                "course_id": 157624,
                "name": "Digital Signals and Filtering",
                "code": "MATH-6767",
                "term": 34,
            },
        ]

        count = 0
        for course in self.fake_courses:
            ret = asyncio.run(
                self.db.add_course(
                    course["course_id"], course["name"], course["code"], course["term"]
                )
            )

            if ret is not None:
                count += 1
        if DEBUG:
            print(f"Added {count} fake courses to database!")

        # insert/give fake users fake classes 'n Canvas stuff, specifically, in the enrollments table.
        asyncio.run(
            self.db.add_enrollment(
                self.fake_user_ids[0],
                self.fake_courses[0]["course_id"],
                "professor",
                self.fake_discord_server.id,
            )
        )
        asyncio.run(
            self.db.add_enrollment(
                self.fake_user_ids[0],
                self.fake_courses[0]["course_id"],
                "student",
                self.fake_discord_server.id,
            )
        )
        asyncio.run(
            self.db.add_enrollment(
                self.fake_user_ids[1],
                self.fake_courses[1]["course_id"],
                "student",
                self.fake_discord_server.id,
            )
        )
        asyncio.run(
            self.db.add_enrollment(
                self.fake_user_ids[1],
                self.fake_courses[3]["course_id"],
                "student",
                self.fake_discord_server.id,
            )
        )
        asyncio.run(
            self.db.add_enrollment(
                self.fake_user_ids[1],
                self.fake_courses[2]["course_id"],
                "professor",
                self.fake_discord_server.id,
            )
        )

    def tearDown(self) -> None:
        super().tearDown()

        asyncio.run(self.db.close())
        Path(DB_PATH).unlink(missing_ok=False)

        if DEBUG:
            print("Teardown ran successfully!")

    # === individual method tests below this line ===
    # positive tests
    def test_sendAnnouncementPing(self):
        # with professor role, all correct input, should pass
        ret = asyncio.run(
            setup_announcements.callback(
                self.interaction,  # type: ignore
                self.fake_courses[0]["course_id"],
                self.fake_discord_channels[0], # type: ignore
                True,  # type: ignore
            )
        )

        # check that the function thinks it passed
        self.assertTrue(ret)

        # check that it sent the correct output
        # TODO

    def test_setupAnnouncementNoPing(self):
        # with professor role, all correct input, should pass
        # TODO copy from above
        pass

    # negative tests (incorrect input, we want to produce every command failure message)
    # not in the discord server
    # channel doesn't exist
    # discord bot not in channel
    # bot doesn't have channel permissions
    # canvas credentials not linked
    # user not enrolled in course
    # user enrolled in course, but not a professor

    # play stupid games, win stupid prizes tests (can't actually happen irl, but we have to have them anyways)
    # malformed Interaction
    # malformed User in the Interaction
    # user not in DB ??
    # canvas data is like, incorrect? we don't check that though. not my problem.
