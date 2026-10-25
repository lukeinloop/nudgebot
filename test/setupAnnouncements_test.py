"""
NudgeBot: Canvas Integration / Discord Bot

Originally written for the CS-3203 Software Engineering class at the University of Oklahoma in Fall 2026.

Copyright 2026 Group K: Luke Sewell, Janes Le, Daniel Brown. Not open source. All rights reserved.
"""

from pathlib import Path
import unittest
import asyncio
import random
from unittest.mock import MagicMock, patch

import discord
from database.backend import DBHandler
import bot
from bot.bot import setup_announcements, NudgeBot

import uuid

DB_PATH = "./test_database.sqlite"
DEBUG = False

class TestSetupAnnouncements(unittest.TestCase):
    def setUp(self):
        super().setUp()
        
        # also patch the client object in the bot, because obviously it's uninitialized as we don't directly import the module,
        # we only care about the setup_announcements function.
        patch.object(bot.bot, "client", autospec=NudgeBot, create=True).start()  # type: ignore
        bot.bot.client.user = MagicMock(autospec=discord.User)  # type: ignore
        bot.bot.client.user.id = 693993751  # type: ignore
        bot.bot.client.user.name = "NudgeBot"  # type: ignore

        # delete old test DB if it is still there
        Path(DB_PATH).unlink(missing_ok=True)

        self.db = DBHandler(DB_PATH, "./test_key.key")
        asyncio.run(self.db.connect())
        asyncio.run(self.db.initialize_db())

        # TODO what's the point of making a separate DB handler if we're just going to use the real one anyways?
        bot.bot.client.db = self.db  # type: ignore

        # ensure all following INFO prints are on good lines
        if DEBUG:
            print()

        # I did a lot of work and research in trying to create real (not mocked) objects for all of these,
        # to ensure that it would actually be a useful unit test, but unfortunately the library is just not set up for that.
        # if it looks more doable in the future, or somebody has time, look back in the commit history for this file,
        # specifically on the feat/canvas-announcements branch, to get an idea of how you might be able to do it.

        self.fake_discord_server = MagicMock(discord.Guild, autospec=True)
        self.fake_discord_server.id = 123456789

        # discord server that the bot is not in
        self.evil_discord_server = MagicMock(discord.Guild, autospec=True)
        self.evil_discord_server.id = 3141592653

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
            # SQL indices must start at 1
            random.randint(1000, 10000): MagicMock(discord.User, autospec=True),
            random.randint(1000, 10000): MagicMock(discord.User, autospec=True),
            random.randint(1000, 10000): MagicMock(discord.User, autospec=True),
            random.randint(1000, 10000): MagicMock(discord.User, autospec=True),
            random.randint(1000, 10000): MagicMock(discord.User, autospec=True),
            random.randint(1000, 10000): MagicMock(discord.User, autospec=True),
        }

        count = 0
        for id, user in self.fake_discord_users.items():
            count += 1
            user.id = id
            user.name = f"Test User {count}"

        # add the bot as a user as well, so it gets added to the Guild / channels
        self.fake_discord_users[bot.bot.client.user.id] = bot.bot.client.user  # type: ignore

        # make fake interactions
        self.interaction = MagicMock(discord.Interaction, autospec=True)

        # fake canvas api tokens
        self.fake_access_tokens = {
            id: str(uuid.uuid4()) for id, user in self.fake_discord_users.items()
        }

        # fake methods
        def get_member(user_id: int) -> discord.Member:
            return self.fake_discord_users[user_id]

        self.permissions = discord.Permissions()

        def permissions_for(member: discord.Member) -> discord.Permissions:
            return self.permissions

        # keep track of last message
        self.last_message = ""

        async def send_message(message: str, **kwargs) -> None:
            if DEBUG:
                print(f"Fake message sent: {message}")
            self.last_message = message

        self.interaction.response = MagicMock(
            discord.InteractionResponse, autospec=True
        )
        self.interaction.response.send_message = send_message

        # add all of the fake data to the fake server
        self.fake_discord_server.channels = self.fake_discord_channels.values()
        self.fake_discord_server.get_member = get_member

        for id, channel in self.fake_discord_channels.items():
            # give the channel data
            channel.id = id
            channel.name = f"Test Channel {id}"

            # add the guild to each channel
            channel.guild = self.fake_discord_server

            # setup permissions for each channel
            # TODO
            channel.permissions_for = permissions_for

        self.interaction.guild = self.fake_discord_server

        # ========= set up the test database with fake data =========
        # create fake users
        count = 0
        self.fake_user_ids = []  # internal DB IDs
        for id, fake_discord_user in self.fake_discord_users.items():
            # give them API tokens EXCEPT for user 4
            if count == 3:
                continue

            internal_id = asyncio.run(
                self.db.create_user(fake_discord_user.id, fake_discord_user.name)
            )

            self.fake_user_ids.append(internal_id)

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

        # add user 1 to all classes as a professor
        for course in self.fake_courses:
            asyncio.run(
                self.db.add_enrollment(
                    self.fake_user_ids[0],
                    course["course_id"],
                    "professor",
                    self.fake_discord_server.id,
                )
            )

        # add user 2 to all classes as a student
        for course in self.fake_courses:
            asyncio.run(
                self.db.add_enrollment(
                    self.fake_user_ids[1],
                    course["course_id"],
                    "student",
                    self.fake_discord_server.id,
                )
            )

        # add user 3 to half of the classes
        for course in self.fake_courses[:2]:
            asyncio.run(
                self.db.add_enrollment(
                    self.fake_user_ids[2],
                    course["course_id"],
                    "professor",
                    self.fake_discord_server.id,
                )
            )

        # add user 4 to the other half
        # except actually don't because they aren't supposed to be in the DB
        # for course in self.fake_courses[2:]:
        #     asyncio.run(
        #         self.db.add_enrollment(
        #             self.fake_user_ids[3],
        #             course["course_id"],
        #             "student",
        #             self.fake_discord_server.id,
        #         )
        #     )

        # add user 5 as a TA to the 2nd half of classes
        for course in self.fake_courses[2:]:
            asyncio.run(
                self.db.add_enrollment(
                    self.fake_user_ids[4],
                    course["course_id"],
                    "TA",
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
        # test user 1
        self.interaction.user = list(self.fake_discord_users.values())[0]

        # with professor role, all correct input, should pass
        ret = asyncio.run(
            setup_announcements.callback(
                self.interaction,
                self.fake_courses[0]["course_id"],
                self.fake_discord_channels[0],
                True,  # type: ignore
            )
        )

        # check that the function thinks it passed
        self.assertTrue(ret)

        # check that it sent the correct output
        self.assertTrue(
            "announcements successfully set up for course" in self.last_message.lower()
        )

        # TODO: if we have more time, it would be prudent to check that the DB entry in the announcements table is actually there,
        # with the correct information, but since this is just for the assignment (and tbf the book did say only one assert per test as a guideline),
        # I don't honestly think it matters that much.

    # same as above, but with ping set to False. DB entry should thus only be different by a single column
    def test_setupAnnouncementNoPing(self):
        # test user 1
        self.interaction.user = list(self.fake_discord_users.values())[0]

        # with professor role, all correct input, should pass
        ret = asyncio.run(
            setup_announcements.callback(
                self.interaction,
                self.fake_courses[0]["course_id"],
                self.fake_discord_channels[0],
                False,  # type: ignore
            )
        )

        # check that the function thinks it passed
        self.assertTrue(ret)

        # check that it sent the correct output
        self.assertTrue(
            "announcements successfully set up for course" in self.last_message.lower()
        )

    # negative tests (incorrect input, we want to produce every command failure message)
    # not in a discord server
    def test_notInServer(self):
        # test user 1
        self.interaction.user = list(self.fake_discord_users.values())[0]

        self.interaction.guild = None

        # guild field in self.interaction should be None, for instance, if run inside DMs
        ret = asyncio.run(
            setup_announcements.callback(
                self.interaction,
                self.fake_courses[0]["course_id"],
                self.fake_discord_channels[0],
                True,  # type: ignore
            )
        )

        # we expect it to fail
        self.assertFalse(ret)

        # check that it sent the right error message
        self.assertTrue("not in server" in self.last_message.lower())

    # channel doesn't exist
    def test_channelNotExist(self):
        # test user 1
        self.interaction.user = list(self.fake_discord_users.values())[0]

        # channel specified in the command does not exist
        external_channel = MagicMock(discord.TextChannel, autospec=True)
        external_channel.id = -23486234

        # this will in the future hopefully not be possible user-side, with proper autocomplete,
        # but just to be safe, /setup_announcements runs a check on it
        ret = asyncio.run(
            setup_announcements.callback(
                self.interaction,
                self.fake_courses[0]["course_id"],
                external_channel,
                True,  # type: ignore
            )
        )

        # we expect it to fail
        self.assertFalse(ret)

        # check that it sent the correct error message
        self.assertTrue("channel does not exist" in self.last_message.lower())

    # discord bot not in channel
    def test_botNotInChannel(self):
        # test user 1
        self.interaction.user = list(self.fake_discord_users.values())[0]

        def dont_get_member(id: int):
            return None

        # discord bot is not in the channel
        self.fake_discord_server.get_member = dont_get_member

        ret = asyncio.run(
            setup_announcements.callback(
                self.interaction,
                self.fake_courses[0]["course_id"],
                self.fake_discord_channels[0],
                True,  # type: ignore
            )
        )

        # we expect it to fail
        self.assertFalse(ret)

        # check that it sent the correct error message
        self.assertTrue("is not in channel" in self.last_message.lower())

    # bot doesn't have channel permissions
    def test_botNoPermissions(self):
        # test user 1
        self.interaction.user = list(self.fake_discord_users.values())[0]

        # discord bot does not have send permission for channel
        self.permissions = discord.Permissions(send_messages=False)

        ret = asyncio.run(
            setup_announcements.callback(
                self.interaction,
                self.fake_courses[0]["course_id"],
                self.fake_discord_channels[0],
                True,  # type: ignore
            )
        )

        # we expect it to fail
        self.assertFalse(ret)

        # check that it sent the correct error message
        self.assertTrue("does not have permissions" in self.last_message.lower())

    # canvas credentials not linked
    def test_noCanvasCredentials(self):
        # test user 4, who is NOT in the DB
        self.interaction.user = list(self.fake_discord_users.values())[3]

        ret = asyncio.run(
            setup_announcements.callback(
                self.interaction,
                self.fake_courses[0]["course_id"],
                self.fake_discord_channels[0],
                True,  # type: ignore
            )
        )

        # we expect it to fail
        self.assertFalse(ret)

        # check that it sent the correct error message
        self.assertTrue(
            "don't have your canvas credentials" in self.last_message.lower()
        )

    # user not enrolled in course
    def test_notEnrolledInCourse(self):
        # test user 5, who is not in courses 1 and 2
        self.interaction.user = list(self.fake_discord_users.values())[4]

        ret = asyncio.run(
            setup_announcements.callback(
                self.interaction,
                self.fake_courses[1][
                    "course_id"
                ],  # either course 1 or 2 (index 0 or 1)
                self.fake_discord_channels[0],
                True,  # type: ignore
            )
        )

        # we expect it to fail
        self.assertFalse(ret)

        # check that it sent the correct error message
        self.assertTrue(
            "must be enrolled in the course to set up" in self.last_message.lower()
        )

    # user enrolled in course, but not a professor
    def test_notAProfessor(self):
        # test user 2, enrolled in all courses but NOT a professor
        self.interaction.user = list(self.fake_discord_users.values())[1]

        ret = asyncio.run(
            setup_announcements.callback(
                self.interaction,
                self.fake_courses[3]["course_id"],
                self.fake_discord_channels[0],
                True,  # type: ignore
            )
        )

        # we expect it to fail
        self.assertFalse(ret)

        # check that it sent the correct error message
        self.assertTrue("must be a professor to set up" in self.last_message.lower())

    # ==========================================
    # play stupid games, win stupid prizes tests (can't actually happen irl, but we have to test for them anyways)

    # malformed interaction (guild exists, but channel list empty)
    def test_channelListEmpty(self):
        # test user 1
        self.interaction.user = list(self.fake_discord_users.values())[0]

        # empty the list
        self.fake_discord_server.channels = []

        ret = asyncio.run(
            setup_announcements.callback(
                self.interaction,
                self.fake_courses[0]["course_id"],
                self.fake_discord_channels[0],
                True,  # type: ignore
            )
        )

        # we expect it to fail
        self.assertFalse(ret)

        # check that it sent the correct error message
        self.assertTrue("channel does not exist" in self.last_message.lower())

    # malformed user (user for interaction is None, obviously this could never actually happen)
    def test_notInServer(self):
        self.interaction.user = None

        ret = asyncio.run(
            setup_announcements.callback(
                self.interaction,
                self.fake_courses[0]["course_id"],
                self.fake_discord_channels[0],
                True,  # type: ignore
            )
        )

        # we expect it to fail
        self.assertFalse(ret)

    # client is None (perhaps after disconnected? idk how the function would be called irl with client being None)
    def test_clientIsNone(self):
        bot.bot.client = None

        ret = asyncio.run(
            setup_announcements.callback(
                self.interaction,
                self.fake_courses[0]["course_id"],
                self.fake_discord_channels[0],
                True,  # type: ignore
            )
        )

        # we expect it to fail
        self.assertFalse(ret)
