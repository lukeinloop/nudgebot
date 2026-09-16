# TODO: add like, a standard header with authorship and license here or somethin

# this file was taken from https://github.com/Rapptz/discord.py/blob/v2.7.1/examples/app_commands/basic.py
# also check the documentation at https://discordpy.readthedocs.io/en/stable/interactions/api.html#application-commands
# and the discord docs: https://docs.discord.com/developers/interactions/application-commands


from typing import Optional

import discord
from discord import app_commands


class NudgeBot(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)

        self.guild_id = None

        self.tree = app_commands.CommandTree(self)

    # TODO: document this or something
    async def sync_commands(self):
        if self.guild_id is None:
            return

        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=self.guild_id)
        await self.tree.sync(guild=self.guild_id)


# TODO: replace with actual Intents
intents = discord.Intents.default()
client = NudgeBot(intents=intents)


# TODO: replace this or something this was from the example file
@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print("------")

