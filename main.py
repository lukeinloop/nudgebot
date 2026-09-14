#TODO: add like, a standard header with authorship and license here or somethin

# this file was taken from https://github.com/Rapptz/discord.py/blob/v2.7.1/examples/app_commands/basic.py
# also check the documentation at https://discordpy.readthedocs.io/en/stable/interactions/api.html#application-commands
# and the discord docs: https://docs.discord.com/developers/interactions/application-commands



from typing import Optional

import discord
from discord import app_commands

import os
from dotenv import load_dotenv

# automatically grab environment variables from a .env file in the same folder
load_dotenv()

#TODO fix this ???
MY_GUILD = discord.Object(id=os.environ["GUILD_ID"])


class NudgeBot(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        
        self.tree = app_commands.CommandTree(self)

    #TODO: check if we need to rework this
    # In this basic example, we just synchronize the app commands to one guild.
    # Instead of specifying a guild to every command, we copy over our global commands instead.
    # By doing so, we don't have to wait up to an hour until they are shown to the end-user.
    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

#TODO: replace with actual Intents
intents = discord.Intents.default()
client = NudgeBot(intents=intents)

# === actual app commands are below ===

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')


@client.tree.command()
async def hello(interaction: discord.Interaction):
    """Says hello!"""
    await interaction.response.send_message(f'Hi, {interaction.user.mention}')


@client.tree.command()
@app_commands.describe(
    first_value='The first value you want to add something to',
    second_value='The value you want to add to the first value',
)
async def add(interaction: discord.Interaction, first_value: int, second_value: int):
    """Adds two numbers together."""
    await interaction.response.send_message(f'{first_value} + {second_value} = {first_value + second_value}')


# The rename decorator allows us to change the display of the parameter on Discord.
# In this example, even though we use `text_to_send` in the code, the client will use `text` instead.
# Note that other decorators will still refer to it as `text_to_send` in the code.
@client.tree.command()
@app_commands.rename(text_to_send='text')
@app_commands.describe(text_to_send='Text to send in the current channel')
async def send(interaction: discord.Interaction, text_to_send: str):
    """Sends the text into the current channel."""
    await interaction.response.send_message(text_to_send)


# To make an argument optional, you can either give it a supported default argument
# or you can mark it as Optional from the typing standard library. This example does both.
@client.tree.command()
@app_commands.describe(member='The member you want to get the joined date from; defaults to the user who uses the command')
async def joined(interaction: discord.Interaction, member: Optional[discord.Member] = None):
    """Says when a member joined."""
    # If no member is explicitly provided then we use the command user here
    user = member or interaction.user

    # Tell the type checker that this is a Member
    assert isinstance(user, discord.Member)

    # The format_dt function formats the date time into a human readable representation in the official client
    # Joined at can be None in very bizarre cases so just handle that as well
    if user.joined_at is None:
        await interaction.response.send_message(f'{user} has no join date.')
    else:
        await interaction.response.send_message(f'{user} joined {discord.utils.format_dt(user.joined_at)}')


# A Context Menu command is an app command that can be run on a member or on a message by
# accessing a menu within the client, usually via right clicking.
# It always takes an interaction as its first parameter and a Member or Message as its second parameter.


# This context menu command only works on members
@client.tree.context_menu(name='Show Join Date')
async def show_join_date(interaction: discord.Interaction, member: discord.Member):
    # The format_dt function formats the date time into a human readable representation in the official client
    # Joined at can be None in very bizarre cases so just handle that as well

    if member.joined_at is None:
        await interaction.response.send_message(f'{member} has no join date.')
    else:
        await interaction.response.send_message(f'{member} joined at {discord.utils.format_dt(member.joined_at)}')


# This context menu command only works on messages
@client.tree.context_menu(name='Report to Moderators')
async def report_message(interaction: discord.Interaction, message: discord.Message):
    # We're sending this response message with ephemeral=True, so only the command executor can see it
    await interaction.response.send_message(
        f'Thanks for reporting this message by {message.author.mention} to our moderators.', ephemeral=True
    )

    # Make sure that we're inside a guild
    if interaction.guild is None:
        await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
        return

    # Handle report by sending it into a log channel
    log_channel = interaction.guild.get_channel(0)  # replace with your channel id

    if log_channel is None or not isinstance(log_channel, discord.abc.Messageable):
        await interaction.response.send_message('Log channel not found or not messageable.', ephemeral=True)
        return

    embed = discord.Embed(title='Reported Message')
    if message.content:
        embed.description = message.content

    embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
    embed.timestamp = message.created_at

    url_view = discord.ui.View()
    url_view.add_item(discord.ui.Button(label='Go to Message', style=discord.ButtonStyle.url, url=message.jump_url))

    await log_channel.send(embed=embed, view=url_view)


client.run(os.environ["TOKEN"])