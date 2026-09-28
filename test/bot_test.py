import unittest

import discord

from bot.bot import NudgeBot


class TestBackend(unittest.TestCase):
    def setUp(self):
        super().setUp()

        self.bot = NudgeBot(intents=discord.Intents.all())

    # === individual method tests below this line ===
