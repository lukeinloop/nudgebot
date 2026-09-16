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


# Link command to get and store canvas API token
@client.tree.command()
async def link(interaction: discord.Interaction):
    """Securely link your Canvas and Discord accounts."""

    # Ask for API token in DMs so there is no risk of it being exposed in a server
    if interaction.user.dm_channel is None:
        await interaction.user.create_dm()

    # TODO: might need a try/catch around this if not open DMs?
    await interaction.user.dm_channel.send(
        f"""TODO: insert instructions for locating your canvas API token (with screenshots preferably) here.
        Please respond to this message with your API token."""
    )


# !!! THIS IS ONLY FOR INTERACTING IN DMS !!!
# !!! EVERYTHING ELSE SHOULD BE HANDLED THROUGH A SLASH COMMAND !!!
@client.event
async def on_message(message: discord.Message):
    # first check and see if we are triggering on ourself
    if message.author.id == client.user.id:
        return

    if message.channel.type == discord.DMChannel:
        # this is someone trying to give us their API token, so store it or something

        print(f"Got API token: {message.content}")

        pass  # TODO

    # otherwise, do nothing
    # FIXME do we want to have them able to ask for help in DMs as well?
