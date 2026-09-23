# this file was modified from: https://github.com/Rapptz/discord.py/blob/v2.7.1/examples/app_commands/basic.py

from typing import Optional

import discord
from discord import app_commands
import httpx

from database.backend import DBHandler


class NudgeBot(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)

        self.guild_id: None | discord.Object = None
        self.db: DBHandler = None

        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        if self.guild_id is None:
            return

        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=self.guild_id)
        await self.tree.sync(guild=self.guild_id)


intents = discord.Intents.all()
client = NudgeBot(intents=intents)


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

    assert interaction.user.dm_channel is not None
    await interaction.user.dm_channel.send(
        f"""Go to your canvas settings and generate a new Access Token. Copy and paste the Access Token below and send it."""
    )

    await interaction.response.send_message(
        "Please check your DMs for further instructions!"
    )

# Courses command to get course list
@client.tree.command
async def courses(interaction: discord.Interaction):
    await interaction.response.defer(ephermal=True)

    
    api_key = await client.db.has_api_key(interaction.user.id)

    if not api_key:
        await interaction.followup.send(
            "You haven't linked your Canvas account yet. Use /link to get started.", 
            ephemeral=True
        )
        return

    url = "https://canvas.ou.edu/api/v1/courses"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"per_page": 20, "enrollment_state": "active"}

    try:
        # async client since discord.py is asynchronous
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(url, headers=headers, params=params)
            response.raise_for_status()
            courses_data = response.json()

        if not courses_data:
            await interaction.followup.send("No active courses found.", ephemeral=True)
            return

        message_lines = []
        for course in courses_data:
            course_name = course.get("name") or course.get("course_code", "Unnamed Course")
            message_lines.append(f"• **{course_name}** (ID: `{course.get('id')}`)")

        # Send the finalized list
        await interaction.followup.send("\n".join(message_lines), ephemeral=True)

    except httpx.HTTPStatusError as e:
        await interaction.followup.send(
            f"Failed to retrieve courses. Canvas API returned error status: {e.response.status_code}", 
            ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(
            "An unexpected error occurred.", 
            ephemeral=True
        )




# !!! THIS IS ONLY FOR INTERACTING IN DMS !!!
# !!! EVERYTHING ELSE SHOULD BE HANDLED THROUGH A SLASH COMMAND !!!
@client.event
async def on_message(message: discord.Message):
    # first check and see if we are triggering on ourself
    assert client.user is not None

    if message.author.id == client.user.id:
        return

    if type(message.channel) == discord.DMChannel:
        # this is someone trying to give us their API token, so store it

        if not await client.db.user_exists(message.author.id):
            await client.db.create_user(message.author.id, message.author.display_name)

        # replace / update API key
        await client.db.add_api_key(
            message.author.id, "https://canvas.ou.edu/", message.content.strip()
        )

    # otherwise, do nothing
    return
