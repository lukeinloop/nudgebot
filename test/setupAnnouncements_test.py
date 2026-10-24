"""
NudgeBot: Canvas Integration / Discord Bot

Originally written for the CS-3203 Software Engineering class at the University of Oklahoma in Fall 2026.

Copyright 2026 Group K: Luke Sewell, Janes Le, Daniel Brown. Not open source. All rights reserved.
"""

import json
from json import dumps as _dumps

from pathlib import Path
from typing import Callable
import unittest
import asyncio
from unittest.mock import MagicMock, patch

import discord
from discord.state import ConnectionState
from discord.http import HTTPClient
from database.backend import DBHandler
import bot
from bot.bot import intents, NudgeBot, setup_announcements

# FIXME do we need a separate test case for announcement polling?
DB_PATH = "./test_database.sqlite"
DEBUG = False


# patch json module function 'dumps' to work with MagicMock objects
# as, obviously, we can't alter the code being called for the object in wherever it's getting called.
# taken from SO answer: https://stackoverflow.com/questions/73989150/how-to-make-a-python-magicmock-object-json-serializable
def dumps_wrapper(*args, **kwargs):
    return _dumps(*args, **(kwargs | {"default": lambda obj: "mock"}))


json.dumps = MagicMock(wraps=dumps_wrapper)
patch("json.dumps", MagicMock(wraps=dumps_wrapper))


# patch the send_message function, since we aren't actually establishing any HTTP connections
# this was actually really hard to figure out and it's insane Python allows you to do this
async def send_message(
    interaction: discord.interactions.InteractionResponse, msg: str, **kwargs
):
    print(f"Sent message: '{msg}' in channel {interaction._parent.channel}")


patch.object(
    discord.interactions.InteractionResponse, "send_message", send_message
).start()

# also need to prevent the Interaction from actually trying to make real discord API calls
# async def _get

# patch(discord.Interaction._state._get_guild).start()

# also patch the client object in the bot, because obviously it's uninitialized as we don't directly import the module,
# we only care about the setup_announcements function.
patch.object(bot.bot, "client", autospec=NudgeBot, create=True).start()  # type: ignore
bot.bot.client.user = MagicMock(autospec=discord.User)
bot.bot.client.user.id = 123456789

class TestSetupAnnouncements(unittest.TestCase):
    def setUp(self):
        super().setUp()

        self.bot = NudgeBot(intents=intents)

        # delete old test DB if it is still there
        Path(DB_PATH).unlink(missing_ok=True)

        self.db = DBHandler(DB_PATH, "./test_key.key")
        asyncio.run(self.db.connect())
        asyncio.run(self.db.initialize_db())

        #TODO what's the point of making a separate DB handler if we're just going to use the real one anyways?
        bot.bot.client.db = self.db

        # ensure all following INFO prints are on good lines
        print()

        # a lot of this is not documented exactly, as you're not supposed to create these manually,
        # so this had to be stolen from types/guild.py
        self.fake_discord_server = discord.Guild(
            data={
                "id": 98456312,
                "name": "Test Guild",
                "icon": None,
                "splash": None,
                "discovery_splash": None,
                "emojis": [],
                "features": [],
                "description": "This is a test guild for testing purposes",
                "incidents_data": None,
                # taken from types/guild.py
                "owner_id": 123456789,
                "region": "US",
                "afk_channel_id": None,
                "afk_timeout": 0,
                "verification_level": 0,
                "default_message_notifications": 0,
                "explicit_content_filter": 0,
                "roles": [],
                "mfa_level": 0,
                "nsfw_level": 0,
                "application_id": None,
                "system_channel_id": None,
                "system_channel_flags": 0,
                "rules_channel_id": None,
                "vanity_url_code": None,
                "banner": None,
                "premium_tier": 0,
                "preferred_locale": "US",
                "public_updates_channel_id": None,
                "stickers": [],
                "stage_instances": [],
                "guild_scheduled_events": [],
                "icon_hash": None,
                "owner": False,
                "permissions": "",
                "widget_enabled": False,
                "widget_channel_id": None,
                "joined_at": None,
                "large": False,
                "member_count": 3,
                "voice_states": [],
                "members": [],  # TODO add members
                "channels": [],  # TODO add channels
                "presences": [],
                "threads": [],
                "max_presences": 0,
                "max_members": 150,
                "premium_subscription_count": 0,
                "max_video_channel_users": 0,
                "soundboard_sounds": [],
            },
            state=ConnectionState(
                dispatch=MagicMock(Callable),
                handlers={"test_handler": MagicMock(Callable)},
                hooks={"on_open": MagicMock(Callable), "on_close": MagicMock(Callable)},
                http=HTTPClient(loop=MagicMock(asyncio.AbstractEventLoop)),
            ),
        )

        # discord server that the bot is not in
        self.evil_discord_server = discord.Guild(
            data={
                "id": 498462651320,
                "name": "Evil Guild",
                "icon": None,
                "splash": None,
                "discovery_splash": None,
                "emojis": [],
                "features": [],
                "description": "This guild doesn't actually exist, nor should anyone be able to see it",
                "incidents_data": None,
                # taken from types/guild.py
                "owner_id": 79854163212,
                "region": "gb",
                "afk_channel_id": None,
                "afk_timeout": 0,
                "verification_level": 0,
                "default_message_notifications": 0,
                "explicit_content_filter": 0,
                "roles": [],
                "mfa_level": 1,
                "nsfw_level": 0,
                "application_id": None,
                "system_channel_id": None,
                "system_channel_flags": 0,
                "rules_channel_id": None,
                "vanity_url_code": None,
                "banner": None,
                "premium_tier": 0,
                "preferred_locale": "FR",
                "public_updates_channel_id": None,
                "stickers": [],
                "stage_instances": [],
                "guild_scheduled_events": [],
                "icon_hash": None,
                "owner": False,
                "permissions": "",
                "widget_enabled": False,
                "widget_channel_id": None,
                "joined_at": None,
                "large": False,
                "member_count": 3,
                "voice_states": [],
                "members": [],
                "channels": [],
                "presences": [],
                "threads": [],
                "max_presences": 0,
                "max_members": 150,
                "premium_subscription_count": 0,
                "max_video_channel_users": 0,
                "soundboard_sounds": [],
            },
            state=ConnectionState(
                dispatch=MagicMock(Callable),
                handlers={"test_handler": MagicMock(Callable)},
                hooks={"on_open": MagicMock(Callable), "on_close": MagicMock(Callable)},
                http=HTTPClient(loop=MagicMock(asyncio.AbstractEventLoop)),
            ),
        )

        # fake discord channel(s)
        self.fake_discord_channels = {
            0: discord.TextChannel(
                state=MagicMock(ConnectionState),
                guild=self.fake_discord_server,
                data={
                    "id": 87986541,
                    "name": "Test Channel 1",
                    "guild_id": self.fake_discord_server.id,
                    "position": 0,
                    "permission_overwrites": [],
                    "nsfw": False,
                    "parent_id": None,
                    "topic": "This is the good channel that will always work.",
                    "last_message_id": None,
                    "last_pin_timestamp": "",
                    "rate_limit_per_user": 0,
                    "default_thread_rate_limit_per_user": 0,
                    "type": 0,
                },
            ),
            1: discord.TextChannel(
                state=MagicMock(ConnectionState),
                guild=self.fake_discord_server,
                data={
                    "id": 5468521,
                    "name": "Test Channel 2",
                    "guild_id": self.fake_discord_server.id,
                    "position": 2,
                    "permission_overwrites": [],
                    "nsfw": False,
                    "parent_id": None,
                    "topic": "Very yes, much topic. There is topic yes believe me. This is the evil channel.",
                    "last_message_id": None,
                    "last_pin_timestamp": "",
                    "rate_limit_per_user": 0,
                    "default_thread_rate_limit_per_user": 0,
                    "type": 0,
                },
            ),
            2: discord.TextChannel(
                state=MagicMock(ConnectionState),
                guild=self.evil_discord_server,
                data={
                    "id": 693993751,
                    "name": "Evil Cannel",
                    "guild_id": self.evil_discord_server.id,
                    "position": 0,
                    "permission_overwrites": [],
                    "nsfw": True,
                    "parent_id": None,
                    "topic": "This channel is not part of the good discord server.",
                    "last_message_id": -1,
                    "last_pin_timestamp": "",
                    "rate_limit_per_user": 0,
                    "default_thread_rate_limit_per_user": 0,
                    "type": 0,
                },
            ),
        }
        # HACK evil force assign channels to the guild
        self.fake_discord_server._channels = self.fake_discord_channels

        # fake discord users
        self.fake_discord_users = [
            discord.User(
                state=MagicMock(ConnectionState),
                data={
                    "id": 984651321,
                    "username": "Test User 1",
                    "discriminator": "testuser134234",
                    "avatar": None,
                    "global_name": None,
                    "avatar_decoration_data": None,
                    "primary_guild": None,
                    "collectibles": None,
                    "bot": False,
                    "system": False,
                    "mfa_enabled": False,
                    "locale": "US",
                    "verified": True,
                    "email": None,
                    "flags": 999999999,
                    "premium_type": 0,
                    "public_flags": 9999999,
                },  # type: ignore
            ),
            discord.User(
                state=MagicMock(ConnectionState),
                data={
                    "id": 641313,
                    "username": "Test User 2",
                    "discriminator": "testuser31415",
                    "avatar": None,
                    "global_name": None,
                    "avatar_decoration_data": None,
                    "primary_guild": None,
                    "collectibles": None,
                    "bot": False,
                    "system": False,
                    "mfa_enabled": False,
                    "locale": "US",
                    "verified": True,
                    "email": None,
                    "flags": 999999999,
                    "premium_type": 0,
                    "public_flags": 9999999,
                },  # type: ignore
            ),
            discord.User(
                state=MagicMock(ConnectionState),
                data={
                    "id": 14652312,
                    "username": "Evil User 1",
                    "discriminator": "IamSoEvil",
                    "avatar": None,
                    "global_name": None,
                    "avatar_decoration_data": None,
                    "primary_guild": None,
                    "collectibles": None,
                    "bot": False,
                    "system": False,
                    "mfa_enabled": False,
                    "locale": "US",
                    "verified": False,
                    "email": None,
                    "flags": 999999999,
                    "premium_type": 0,
                    "public_flags": 9999999,
                },  # type: ignore
            ),
        ]
        # add the bot itself as a user too
        self.fake_discord_users.append(
            discord.User(
                state=MagicMock(ConnectionState),
                data={
                    "id": bot.bot.client.user.id,
                    "username": "Bot User",
                    "discriminator": "discriminator",
                    "avatar": None,
                    "global_name": None,
                    "avatar_decoration_data": None,
                    "primary_guild": None,
                    "collectibles": None,
                    "bot": True,
                    "system": False,
                    "mfa_enabled": False,
                    "locale": "US",
                    "verified": True,
                    "email": None,
                    "flags": 999999999,
                    "premium_type": 0,
                    "public_flags": 9999999,
                },  # type: ignore
            ),
        )

        # add fake members to the fake discord server
        self.fake_discord_members = {}
        for user in self.fake_discord_users:
            self.fake_discord_members[user.id] = discord.Member(
                data={
                    "roles": [],
                    "joined_at": "1970-01-01 01:01",
                    "deaf": False,
                    "mute": False,
                    "flags": 0,
                    "avatar": "no avatar",
                    "user": user,
                    "nick": user.name,
                    "premium_since": None,
                    "pending": False,
                    "permissions": 0,
                    "communication_disabled_until": "",
                    "banner": None,
                    "avatar_decoration_data": None,
                },
                guild=self.fake_discord_server,
                state=MagicMock(ConnectionState),
            )
        
        self.fake_discord_server._members = self.fake_discord_members
        self.fake_discord_server._member_count = len(self.fake_discord_members)
        if DEBUG:
            print("Discord members:")
            [print(m) for m in self.fake_discord_members]

        # make fake interactions
        self.interaction = discord.Interaction(
            data={
                "app_permissions": 2**16,
                "application_id": 1547277112627429458,  # this one is real
                # "channel": self.fake_discord_channels[0],
                "channel_id": self.fake_discord_channels[0].id,
                "client": None,
                "command": setup_announcements,
                "command_failed": False,
                "command_id": 0,  # TODO FIXME
                "context": discord.AppCommandContext(
                    guild=True, dm_channel=True, private_channel=True
                ),
                "created_at": None,
                "custom_id": None,
                "data": {

                },
                "entitlement_sku_ids": [],
                "entitlements": [],
                "expires_at": None,
                "extras": [],
                "attachment_size_limit": 0,
                "followup": None,
                "guild": self.fake_discord_server,
                "guild_id": self.fake_discord_server.id,
                "guild_locale": "US",
                "id": 19846,
                "locale": "US",
                "message": {"id": 65749846},
                "namespace": None,
                "permissions": [],
                "response": MagicMock(
                    autospec=discord.InteractionCallbackResponse, create=True
                ),
                "token": None,
                "type": None,
                "user": None,
                "version": 1,
            },  # type: ignore
            #TODO FIXME this state needs to have its _get_guild() (and probably a lot of other things too) replaced with like return False or something? or have _state set to False? idk how you are supposed to do it
            state=MagicMock(autospec=ConnectionState, create=True),
        )

        # override the magicmock auto-created attribute
        def get_guild(guild_id: int):
            return self.fake_discord_server
        self.interaction._state._get_guild = get_guild # type: ignore

        # override this auto-created attribute too
        self.interaction_user = None
        def get_user():
            return self.interaction_user
        self.interaction._state.get_user = get_user # type: ignore


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
        for fake_discord_user in self.fake_discord_users:
            ret = asyncio.run(
                self.db.create_user(fake_discord_user.id, fake_discord_user.name)
            )

            if ret is not None:
                count += 1
        if DEBUG:
            print(f"Initialized DB with {count} fake users")

        # give them fake API tokens
        count = 0
        for i, fake_discord_user in enumerate(self.fake_discord_users):
            # TODO make add_api_key return something other than None
            ret = asyncio.run(
                self.db.add_api_key(
                    fake_discord_user.id,
                    "https://canvas.ou.edu/",
                    self.fake_access_tokens[i],
                )
            )

            count += 1
        if DEBUG:
            print(f"Added {count} fake access tokens")

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

        # get internal user IDs (yes we should just make test objects, it can be a PBI)
        self.fake_user_ids = []
        for user in self.fake_discord_users:
            user_row = asyncio.run(self.db.get_user(user.id))

            if user_row is not None:
                user_id = user_row[0]
                self.fake_user_ids.append(user_id)
        if DEBUG:
            print(f"Found {len(self.fake_user_ids)} users in the database!")

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
        # add the custom interaction data for this test case
        self.interaction.channel = self.fake_discord_channels[0]
        assert self.interaction.guild is not None
        self.interaction.guild._channels = self.fake_discord_channels # type: ignore

        self.interaction.user = self.fake_discord_members[self.fake_discord_users[0].id]
        self.interaction_user = self.interaction.user
        self.interaction._state._users = self.fake_discord_users


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


"""
Unit 1: setup_announcements(interaction: Discord.interaction, course_id, ping=True, channel: Optional[discord.Channel] = None)
 * correct: interaction is valid from Discord, initiated by a Discord user in the database, who has linked Canvas credentials with a "professor" role for the course_id, the course_id is valid and exists, the channel exists
 * incorrect: interaction object is missing data/malformed, course_id isn't a positive integer, channel isn't a discord Channel object
 * boundary condition: interaction object must have the user and channel if channel is not specified, the channel doesn't exist
 * edge cases: Discord user isn't in databse, doesn't have professor role for the specified course, course doesn't exist, the channel isn't public/bot doesn't have persmissions to view it, 
"""
