"""
NudgeBot: Canvas Integration / Discord Bot

Originally written for the CS-3203 Software Engineering class at the University of Oklahoma in Fall 2026.

Copyright 2026 Group K: Luke Sewell, Janes Le, Daniel Brown. Not open source. All rights reserved.
"""

import unittest

import discord

from bot.bot import intents, NudgeBot

#FIXME do we need a separate test case for announcement polling?

class TestAnnouncements(unittest.TestCase):
    def setUp(self):
        super().setUp()

        self.bot = NudgeBot(intents=intents)

        self.test_guild: discord.Guild #TODO FIXME
        self.test_channel: discord.TextChannel #TODO FIXME

    # === individual method tests below this line ===
    # positive tests
    def test_sendAnnouncementPing(self):
        testAnnouncement = "Hello all, I am feeling sick today and so class is cancelled. I will see you all next Wednesday. -Professor"

        self.bot.sendAnnouncement(testAnnouncement, self.test_channel, ping=True)
        #TODO: any asserts?

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
you have to configure it first, as we know nothing, right?
so in a class discord, in an annoucements channel, you run /setup_announcements <course_id> [ping=True] [channel=current channel]

that adds it to a table in the DB called like announcements with (ID IPK, guild_id, channel_id, course_id, professor_user_id, ping?) and you can grab professor API token from other tables

then poll_for_announcements checks the table that's stored in and then checks the course ID, and sends messages to the correct channel in the correct guild

so to test the /setup_announcements command, we will have:
correct input: good course_id, ping True/False, good channel, all run inside a correct guild with an existing user who has professor credentials in that course ID linked
incorrect input: course_id is wrong/DNE, the channel doesn't exist, the guild doesn't exist, the user isn't linked, doesn't have credentials, isn't a professor, isn't connected to that course ID
boundary conditions: ???
edge cases: ???

Unit 1: setup_announcements(interaction: Discord.interaction, course_id, ping=True, channel: Optional[discord.Channel] = None)
 * correct: interaction is valid from Discord, initiated by a Discord user in the database, who has linked Canvas credentials with a "professor" role for the course_id, the course_id is valid and exists, the channel exists
 * incorrect: interaction object is missing data/malformed, course_id isn't a positive integer, channel isn't a discord Channel object
 * boundary condition: interaction object must have the user and channel if channel is not specified, the channel doesn't exist
 * edge cases: Discord user isn't in databse, doesn't have professor role for the specified course, course doesn't exist, the channel isn't public/bot doesn't have persmissions to view it, 
"""