"""
NudgeBot: Canvas Integration / Discord Bot

Originally written for the CS-3203 Software Engineering class at the University of Oklahoma in Fall 2026.

Copyright 2026 Group K: Luke Sewell, Janes Le, Daniel Brown. Not open source. All rights reserved.
"""

from typing import Callable
import unittest
import asyncio
from unittest.mock import MagicMock

import discord
from discord.state import ConnectionState
from discord.http import HTTPClient
from database.backend import DBHandler
from bot.bot import intents, NudgeBot, setup_announcements

# FIXME do we need a separate test case for announcement polling?


class TestSetupAnnouncements(unittest.TestCase):
    def setUp(self):
        super().setUp()

        self.bot = NudgeBot(intents=intents)

        self.db = DBHandler("./test_database.sqlite", "./test_key.key")
        asyncio.run(self.db.connect())
        asyncio.run(self.db.initialize_db())

        # TODO: make fake discord server
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

        # TODO: fake discord channel(s)
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
                    "topic": "None",
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
                    "topic": "Very yes, much topic. There is topic yes believe me.",
                    "last_message_id": None,
                    "last_pin_timestamp": "",
                    "rate_limit_per_user": 0,
                    "default_thread_rate_limit_per_user": 0,
                    "type": 0,
                },
            ),
            2: None,
        }
        # evil force assign channels to the guild
        self.fake_discord_server._channels = self.fake_discord_channels

        # TODO: fake discord users
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
                },
            ),
            discord.User(
                state=MagicMock(ConnectionState),
                data={
                    "id": 984651321,
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
                },
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
                },
            ),
        ]

        # TODO: make fake interactions

        # insert at least one fake user into the database, as you must
        # have your canvas credentials linked to use the command
        asyncio.run(self.db.add_api_key(self.fake_discord_users[0].id, "https://canvas.ou.edu/", "fake_access_token_1"))
        asyncio.run(self.db.add_api_key(self.fake_discord_users[1].id, "https://canvas.ou.edu/", "fake_access_token_2"))

        # TODO: insert/give fake users fake classes 'n Canvas stuff
        # specifically, in the enrollments table.
        asyncio.run(self.db.add_enrollment()) # one professor
        asyncio.run(self.db.add_enrollment()) # one student

    def tearDown(self) -> None:
        super().tearDown()

        asyncio.run(self.db.close())

    # === individual method tests below this line ===
    # positive tests
    def test_sendAnnouncementPing(self):
        setup_announcements.callback(
            Group, discord.Interaction(), course_id=None, channel=self.fake_discord_channels[0], ping=True
        )
        # TODO

    def test_sendAnnouncementNoPing(self):
        pass

    def test_sendDMAnnouncement(self):
        pass

    # negative tests
    def test_sendEmptyAnnouncement(self):
        pass

    def test_sendTooBigAnnouncement(self):
        pass

    def test_sendNoPermissionsAnnouncement(self):
        pass

    def test_sendAnnouncementNoChannel(self):
        pass

    def test_sendAnnouncementNoUser(self):
        pass


"""
Unit 1: setup_announcements(interaction: Discord.interaction, course_id, ping=True, channel: Optional[discord.Channel] = None)
 * correct: interaction is valid from Discord, initiated by a Discord user in the database, who has linked Canvas credentials with a "professor" role for the course_id, the course_id is valid and exists, the channel exists
 * incorrect: interaction object is missing data/malformed, course_id isn't a positive integer, channel isn't a discord Channel object
 * boundary condition: interaction object must have the user and channel if channel is not specified, the channel doesn't exist
 * edge cases: Discord user isn't in databse, doesn't have professor role for the specified course, course doesn't exist, the channel isn't public/bot doesn't have persmissions to view it, 
"""
