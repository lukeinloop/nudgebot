# this file was modified from: https://github.com/Rapptz/discord.py/blob/v2.7.1/examples/app_commands/basic.py

from typing import Optional
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
import httpx

from database.backend import DBHandler

from bot.assignment_reminders import check_assignment_reminders

class NudgeBot(discord.Client):
    """
    Discord client for NudgeBot.

    This class manages the Discord client, command tree, and database
    connection used by NudgeBot.

    :param intents: The Discord intents that the client should use.
    :type intents: discord.Intents
    """

    def __init__(self, *, intents: discord.Intents):
        """Initialize NudgeBot client.

        :param intents: The Discord intents that the client should use.
        :type intents: discord.Intents
        """
        super().__init__(intents=intents)

        self.guild_id: None | discord.Object = None
        self.db: DBHandler = None

        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        """
        Set up and synchronize NudgeBot's commands.

        If a guild ID has been configured global application commands
        are copied to that guild.
        """
        if self.guild_id is None:
            return

        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=self.guild_id)
        await self.tree.sync(guild=self.guild_id)


intents = discord.Intents.all()
client = NudgeBot(intents=intents)


@client.event
async def on_ready():
    """
    Handle the event triggered when NudgeBot has successfully logged in.

    This event prints NudgeBot's username and Discord ID to the console.
    """
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print("------")


# Link command to get and store canvas API token
@client.tree.command()
async def link(interaction: discord.Interaction):
    """
    "Securely" link the user's Canvas and Discord accounts.

    The user is instructed to generate a Canvas API access token and
    provide it through a direct message. Using direct messages
    prevents the API token from being exposed in a server to others.

    :param interaction: The Discord interaction that triggered the command.
    :type interaction: discord.Interaction
    """

    # Ask for API token in DMs so there is no risk of it being exposed in a server
    if interaction.user.dm_channel is None:
        await interaction.user.create_dm()

    assert interaction.user.dm_channel is not None
    await interaction.user.dm_channel.send(
        f"""Go to your canvas settings and generate a new Access Token. Copy and paste the Access Token below and send it."""
    )

    await interaction.response.send_message(
        "Please check your DMs for further instructions!", ephemeral=True
    )


# Courses command to get course list
@client.tree.command()
async def courses(interaction: discord.Interaction):
    """
    Retrieve and display the user's active Canvas courses.

    The user's stored Canvas API key is retrieved from the database and
    used to request their active courses from the Canvas API. The course
    names and IDs are then displayed in an ephemeral Discord message,
    which hides it from other uses in the server.

    :param interaction: The Discord interaction that triggered the command.
    :type interaction: discord.Interaction
    """
    await interaction.response.defer(ephemeral=True)

    api_key = await client.db.get_api_key(interaction.user.id)

    if not api_key:
        await interaction.followup.send(
            "You haven't linked your Canvas account yet. Use /link to get started.",
            ephemeral=True,
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
            course_name = course.get("name") or course.get(
                "course_code", "Unnamed Course"
            )
            message_lines.append(f"• **{course_name}** (ID: `{course.get('id')}`)")

        # Send the finalized list
        await interaction.followup.send("\n".join(message_lines), ephemeral=True)

    except httpx.HTTPStatusError as e:
        await interaction.followup.send(
            f"Failed to retrieve courses. Canvas API returned error status: {e.response.status_code}",
            ephemeral=True,
        )
    except Exception:
        await interaction.followup.send("An unexpected error occurred.", ephemeral=True)

# Assignments command to get upcoming Canvas assignments
@client.tree.command()
@app_commands.describe(days="Number of days ahead to show assignments",
                       course="Course name to filter assignments by",
)
async def assignments(
    interaction: discord.Interaction,
    days: app_commands.Range[int, 1, 60] = 7,
    course: Optional[str] = None,
):
    """
    Retrieve and display the user's upcoming Canvas assignments.

    The user's stored Canvas API key is used to retrieve upcoming
    assignments from Canvas. Assignments are filtered by the specified
    number of days and can optionally be filtered by course.

    :param interaction: The Discord interaction that triggered the command.
    :type interaction: discord.Interaction
    :param days: Number of days ahead to show upcoming assignments.
    :type days: int
    :param course: Optional course name used to filter assignments.
    :type course: str | None
    """

    await interaction.response.defer(ephemeral=True)

    # Get the user's Canvas API key
    api_key = await client.db.get_api_key(interaction.user.id)

    if not api_key:
        await interaction.followup.send(
            "You haven't linked your Canvas account yet. Use /link to get started.",
            ephemeral=True,
        )
        return

    url = "https://canvas.ou.edu/api/v1/users/self/upcoming_events"
    headers = {"Authorization": f"Bearer {api_key}"}

    courses_url = "https://canvas.ou.edu/api/v1/courses"
    courses_params = {
        "per_page": 100,
        "enrollment_state": "active",
    }

    try:
        async with httpx.AsyncClient() as http_client:
            # Get upcoming assignments
            response = await http_client.get(url, headers=headers)
            response.raise_for_status()
            events = response.json()

            # Get active courses
            courses_response = await http_client.get(
                courses_url,
                headers=headers,
                params=courses_params,
            )
            courses_response.raise_for_status()
            courses_data = courses_response.json()

            course_names = {}

        for canvas_course in courses_data:
            course_id = canvas_course.get("id")
            course_name = canvas_course.get("name") or canvas_course.get(
                "course_code", "Unnamed Course"
            )

            course_names[course_id] = course_name

        now = datetime.now(timezone.utc)
        end_date = now + timedelta(days=days)

        upcoming_assignments = []

        for event in events:
            if event.get("type") != "assignment":
                continue

            assignment = event.get("assignment")

            if not assignment:
                continue

            due_at = assignment.get("due_at")

            if not due_at:
                continue

            due_date = datetime.fromisoformat(
                due_at.replace("Z", "+00:00")
            )

            if not (now <= due_date <= end_date):
                continue

            course_id = assignment.get("course_id")
            course_name = course_names.get(course_id, "Unknown Course")

            # If the user selected a course, only include matching assignments
            if course and course.lower() not in course_name.lower():
                continue

            upcoming_assignments.append(
                (due_date, assignment, course_name)
            )

        upcoming_assignments.sort(key=lambda item: item[0])

        if not upcoming_assignments:
            await interaction.followup.send(
                f"No assignments due in the next {days} days.",
                ephemeral=True,
            )
            return

        if course:
            heading = f"**Upcoming {course} assignments - next {days} days**\n"
        else: 
            heading = f"**Upcoming assignments - next {days} days**\n"

        message_lines = [heading]

        for due_date, assignment, course_name in upcoming_assignments:
            name = assignment.get("name", "Unnamed Assignment")
            assignment_url = assignment.get("html_url")

            timestamp = int(due_date.timestamp())

            message_lines.append(
                f"**{name}**\n"
                f"Course: `{course_name}`\n"
                f"Due: <t:{timestamp}:F> (<t:{timestamp}:R>)\n"
                f"[Open in Canvas]({assignment_url})"
            )

        await interaction.followup.send(
            "\n\n".join(message_lines),
            ephemeral=True,
        )

    except httpx.HTTPStatusError as e:
        await interaction.followup.send(
            f"Failed to retrieve assignments. "
            f"Canvas API returned error status: {e.response.status_code}",
            ephemeral=True,
        )

    except Exception as e:
        print(f"Assignments error: {e}")

        await interaction.followup.send(
            "An unexpected error occurred while retrieving assignments.",
            ephemeral=True,
        )

# Autocomplete function for assigments command
@assignments.autocomplete("course")
async def assignments_course_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    """
    Provide course name suggestions for the assignments command.

    Retrieves the user's active Canvas courses and filters the course
    names based on the text currently entered by the user.

    :param interaction: The Discord interaction that triggered the autocomplete.
    :type interaction: discord.Interaction
    :param current: The current text entered in the course option.
    :type current: str
    :return: A list of matching Canvas course choices.
    :rtype: list[app_commands.Choice[str]]
    """
    api_key = await client.db.get_api_key(interaction.user.id)

    if not api_key:
        return []

    url = "https://canvas.ou.edu/api/v1/courses"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {
        "per_page": 100,
        "enrollment_state": "active",
    }

    try:
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(
                url,
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            courses_data = response.json()

        choices = []

        for canvas_course in courses_data:
            course_name = canvas_course.get("name") or canvas_course.get(
                "course_code", "Unnamed Course"
            )

            if current.lower() in course_name.lower():
                choices.append(
                    app_commands.Choice(
                        name=course_name[:100],
                        value=course_name,
                    )
                )

        return choices[:25]

    except Exception as e:
        print(f"Course autocomplete error: {e}")
        return []


# Reminders command to enable assignment reminders
@client.tree.command()
@app_commands.describe(
    hours="Number of hours before an assignment is due to send a reminder"
)
async def reminders(
    interaction: discord.Interaction,
    hours: app_commands.Range[int, 1, 168] = 24,
):
    """Enable Canvas assignment reminders."""

    # Make sure the user has linked their Canvas account
    api_key = await client.db.get_api_key(interaction.user.id)

    if not api_key:
        await interaction.response.send_message(
            "You haven't linked your Canvas account yet. Use /link to get started.",
            ephemeral=True,
        )
        return

    success = await client.db.enable_reminders(
        interaction.user.id,
        hours,
    )

    if not success:
        await interaction.response.send_message(
            "Could not enable reminders.",
            ephemeral=True,
        )
        return

    await interaction.response.send_message(
        f"Assignment reminders enabled! I'll remind you {hours} hours before an assignment is due.",
        ephemeral=True,
    )

# Temporary command for testing assignment reminders
@client.tree.command()
async def test_reminders(interaction: discord.Interaction):
    """Manually check Canvas for assignment reminders."""

    await interaction.response.defer(ephemeral=True)

    try:
        await check_assignment_reminders(client)

        await interaction.followup.send(
            "Reminder check complete. Check the terminal for results.",
            ephemeral=True,
        )

    except Exception as e:
        print(f"Test reminder error: {e}")

        await interaction.followup.send(
            "An error occurred while checking reminders.",
            ephemeral=True,
        )

# !!! THIS IS ONLY FOR INTERACTING IN DMS !!!
# !!! EVERYTHING ELSE SHOULD BE HANDLED THROUGH A SLASH COMMAND !!!
@client.event
async def on_message(message: discord.Message):
    """
    Process direct messages sent to NudgeBot.

    Direct messages are used to receive and store Canvas API tokens.
    Messages sent in servers are ignored because all other
    functionality is handled through slash commands.

    :param message: The Discord message received by the bot.
    :type message: discord.Message
    """
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
