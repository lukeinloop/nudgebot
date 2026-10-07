"""
NudgeBot: Canvas Integration / Discord Bot

Originally written for the CS-3203 Software Engineering class at the University of Oklahoma in Fall 2026.

Copyright 2026 Group K: Luke Sewell, Janes Le, Daniel Brown. Not open source. All rights reserved.
"""

import unittest

import discord

from bot.bot import NudgeBot


class TestBot(unittest.TestCase):
    def setUp(self):
        super().setUp()

        self.bot = NudgeBot(intents=discord.Intents.all())

    # === individual method tests below this line ===
