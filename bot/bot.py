"""
NudgeBot: Canvas Integration / Discord Bot

Originally written for the CS-3203 Software Engineering class at the University of Oklahoma in Fall 2026.

Copyright 2026 Group K: Luke Sewell, Janes Le, Daniel Brown. Not open source. All rights reserved.
"""

# this file was modified from: https://github.com/Rapptz/discord.py/blob/v2.7.1/examples/app_commands/basic.py

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Optional

import discord
from discord import app_commands
import httpx

from database.backend import DBHandler
from canvas.assignments import submission_status


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

        self.guild_id: discord.Object
        self.db: DBHandler

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


intents = discord.Intents(guilds=True, messages=True, members=True, message_content=True)
client = NudgeBot(intents=intents)


@client.event
async def on_ready():
    """
    Handle the event triggered when NudgeBot has successfully logged in.

    This event prints NudgeBot's username and Discord ID to the console.
    """
    if client.user is not None:
        print(f"Logged in as {client.user} (ID: {client.user.id})")
        print("------")
    else:
        print("Failed to connect!")


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
    params: dict[str, str | int] = {
    "per_page": 20,
    "enrollment_state": "active"
}

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
    courses_params: httpx.QueryParams = httpx.QueryParams({
    "per_page": "100",
    "enrollment_state": "active",
    })

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


# Command to create a priority list of what assignments to do first
@client.tree.command()
@app_commands.describe(days="Number of days ahead to show assignments",
                       course="Course name to filter assignments by",
)
async def priority_list(
    interaction: discord.Interaction,
    days: app_commands.Range[int, 1, 60] = 7,
    course: Optional[str] = None,
):
    """
    Retrieve upcoming Canvas assignments and rank them by priority using createPriorityList().

    Priority is based on assignment point value and deadline urgency.
    In the future point value will be replaced with grade weight. 

    :param interaction: The Discord interaction that triggered the command.
    :type interaction: discord.Interaction
    :param days: Number of days ahead to show upcoming assignments.
    :type days: int
    :param course: Optional course name used to filter assignments.
    :type course: str | None
    """

    await interaction.response.defer(ephemeral=True)

    # Retrieve the user's Canvas API key by using their Discord user ID
    api_key = await client.db.get_api_key(interaction.user.id)

    # If the user has not linked their Canvas account, notify them 
    if not api_key:
        await interaction.followup.send(
            "You haven't linked your Canvas account yet. "
            "Use /link to get started.",
            ephemeral=True,
        )
        return

    # canvas api endpoints
    events_url = "https://canvas.ou.edu/api/v1/users/self/upcoming_events"
    courses_url = "https://canvas.ou.edu/api/v1/courses"

    # authenticate requests to canvas with the user's api key
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    # request up to 100 active courses
    courses_params: dict[str, str | int] = {
        "per_page": 100,
        "enrollment_state": "active",
    }

    try:
        # The 20 second timeout helps prevent requests from hanging
        async with httpx.AsyncClient(timeout=20.0) as http_client:

            # Retrieve the user's upcoming Canvas events
            events_response = await http_client.get(
                events_url,
                headers=headers,
            )

            # raise an exception if canvas returns unsuccessful status
            events_response.raise_for_status()

            # convert json response into python data
            events = events_response.json()

            # Retrieve user's active courses
            courses_response = await http_client.get(
                courses_url,
                headers=headers,
                params=courses_params,
            )

            # Same as above but for courses
            courses_response.raise_for_status()
            courses_data = courses_response.json()

        # Create a dictionary mapping each Canvas course ID to its name
        # Use course code if name doesn't exist otherwise use fallback of "Unnamed Course"
        course_names = {
            canvas_course["id"]: (
                canvas_course.get("name")
                or canvas_course.get("course_code")
                or "Unnamed Course"
            )
            for canvas_course in courses_data
        }

        # Use UTC to compare assignment deadlines
        now = datetime.now(timezone.utc)

        prioritized_assignments = createPriorityList(events, days=days, course=course, now=now, course_names=course_names)

        # if no assignments pass the filters, notify user and stop
        if not prioritized_assignments:
            await interaction.followup.send(
                f"No upcoming assignments found in the next {days} days.",
                ephemeral=True,
            )
            return

        # create a heading that reflects if the user filtered by course
        if course:
            heading = (
                f"**Assignment Priorities: {course}**\n"
                f"Evaluating the next {days} days.\n"
            )
        else:
            heading = (
                f"**Assignment Priorities**\n"
                f"Evaluating the next {days} days.\n"
            )

        # start building the discord message    
        message_lines = [heading]

        # format each assignment as a numbered entry 
        for index, assignment in enumerate(
            prioritized_assignments,
            start=1,
        ):
            # Convert the due date to a Unix timestamp.
            # Discord uses this format to display localized dates and times.
            due_date = assignment["due_date"]

            if not isinstance(due_date, datetime):
                continue

            due_timestamp = int(due_date.timestamp())

            # Extract info needed to display each assignment
            name = str(assignment["name"])
            course_name = str(assignment["course"])
            priority = str(assignment["priority_score"])
            points = str(assignment["points"])
            assignment_url = assignment["url"]

            # Show a link if canvas provides one, otherwise display the plain name
            if assignment_url:
                assignment_title = f"[{name}]({assignment_url})"
            else:
                assignment_title = name

            # add the assignment's name, course, point value, priority score, and deadline to list of message lines
            message_lines.append(
                f"**{index}. {assignment_title}**\n"
                f"Course: `{course_name}`\n"
                f"Points: `{points:g}`\n"
                f"Priority: `{priority:.1f}/100`\n"
                f"Due: <t:{due_timestamp}:F> "
                f"(<t:{due_timestamp}:R>)"
            )

        # Combine the heading and assignment entries into one message, seperating with blank line
        message = "\n\n".join(message_lines)

        # send the priority list as an ephemeral discord message
        await interaction.followup.send(
            message,
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )


    # Error handling
    except httpx.HTTPStatusError as e:
        print(
            f"Canvas API error: {e.response.status_code} "
            f"{e.response.text}"
        )

        await interaction.followup.send(
            "Failed to retrieve assignments. "
            f"Canvas returned HTTP {e.response.status_code}.",
            ephemeral=True,
        )

    except httpx.RequestError as e:
        print(f"Canvas connection error: {e}")

        await interaction.followup.send(
            "Could not connect to Canvas. Please try again later.",
            ephemeral=True,
        )

    except Exception as e:
        print(f"Priorities error: {e}")

        await interaction.followup.send(
            "An unexpected error occurred while calculating priorities.",
            ephemeral=True,
        )

def createPriorityList(assignments: list[dict[str, object]], days: int = 7, course: str | None = None, now: datetime | None = None, course_names: dict[int, str] | None = None) -> list[dict[str, object]]:
    """
    Filter and rank assignments by point value and deadline urgency.

    Args:
        assignments: A list of assignment dictionaries
        days: Number of days to look ahead
        course: Optional course name filter
        now: Current time provided for testing or defaults to current time in UTC

    Returns:
        A list of qualifying assignments sorted by highest priority first
    """

    if course_names is None:
        course_names = {}

    # Allow tests to provide a fixed time for consistent results.
    if now is None:
        now = datetime.now(timezone.utc)

    # Calculate the end of the requested assignment search window
    end_date = now + timedelta(days=days)

    # these weights can be adjusted later, together they add up to 1.0
    GRADE_WEIGHT = 0.60
    URGENCY_WEIGHT = 0.40

    # Array for assignments that pass the filters as well as their scores
    prioritized_assignments: list[dict[str, object]] = []

    # examine each event returned by the Canvas API
    for event in assignments:

        # Ignore events that are not assignments
        if event.get("type") != "assignment":
            continue

        # retrieve the details associated with assignment
        assignment_data = event.get("assignment")

        # skip any event that doesnt contain assignment info
        if not isinstance(assignment_data, dict):
            continue

        assignment: dict[str, object] = assignment_data

        # retrieve assignment due date
        due_at = assignment.get("due_at")

        # skip assignments without a due date as they dont have any priority 
        if not isinstance(due_at, str):
            continue

        # convert canvas's ISO 8601 due-date string to a datetime object
        due_date = datetime.fromisoformat(
            due_at.replace("Z", "+00:00")
        )

        # Only consider upcoming assignments in the requested window, past due assignments are not included
        if not now.date() <= due_date.date() <= end_date.date():
            continue

        # retrieve course id that contains this assignment
        course_id = assignment.get("course_id")

        if not isinstance(course_id, int):
            continue

        # look up the course name using the ID
        course_name = course_names.get(
            course_id,
            "Unknown Course",
        )

        # apply the optional course filter
        if course and course.lower() not in course_name.lower():
            continue    

        # ignore assignments that have already been submitted
        if assignment.get("has_submitted_submissions", False):
            continue

        # retrieve # of points available for the assignment
        points_possible = assignment.get("points_possible")

        # missing or invalid point values should not crash the command
        if not isinstance(points_possible, (int, float)):
            points_possible = 0.0

        # convet point value to float and prevent negative numbers from reducing assignment priority
        points_possible = max(float(points_possible), 0.0)

        # normalize assignment importance to a number between 0 and 1
        # Higher point assignments receive a higher score
        # Dividing by (points_possible + 100) prevents the score from increasing linearly without limit
        # For example a 100 point assignment receives a score of 0.5
        grade_score = points_possible / (
            points_possible + 100.0
        )

        # calculate the number of days until the deadline, max() prevnets negative values
        hours_remaining = max(
            (due_date - now).total_seconds() / 3600,
            0,
        )

        # convert remaining time from hours to days
        days_remaining = hours_remaining / 24

        # urgency rises as the deadline approaches (at days_remaining 0 this equals 1, which is the highest priority)
        urgency_score = 1 / (days_remaining + 1)

        # Combine grade importance and urgency using the assigned weights then multiply by 100 for a score out of 100   
        priority_score = 100 * (
            GRADE_WEIGHT * grade_score
            + URGENCY_WEIGHT * urgency_score
        )
        name = assignment.get("name")
        if not isinstance(name, str):
            name = "Unnamed Assignment"

        assignment_url = assignment.get("html_url")
        if not isinstance(assignment_url, str):
            assignment_url = None

        # save assignment details and caluclated scores for sorting and displaying in response on discord
        prioritized_assignments.append({
            "name": name,
            "course": course_name,
            "due_date": due_date,
            "url": assignment_url,
            "points": points_possible,
            "grade_score": grade_score,
            "urgency_score": urgency_score,
            "priority_score": priority_score,
        })

    # Sort by highest priority first
    # if two assignments have the same score, later date comes first because the secondary sort key is reversed
    prioritized_assignments.sort(
        key=lambda assignment: (
            assignment["priority_score"],
            assignment["due_date"],
        ),
        reverse=True,
    )

    return prioritized_assignments
        
# Submissions command to show whether assignments were submitted, late, or missing
@client.tree.command()
@app_commands.describe(
    days="Number of days before and after today to check",
    course="Course name to filter assignments by",
)
async def sub_missions(
    interaction: discord.Interaction,
    days: app_commands.Range[int, 1, 60] = 7,
    course: Optional[str] = None,
):
    """
    Show the submission status of the user's recent and upcoming assignments.

    Assignments due within the given number of days before or after today
    are checked. Each one is labeled as submitted, submitted late, or not
    submitted using submission_status().

    :param interaction: The Discord interaction that triggered the command.
    :type interaction: discord.Interaction
    :param days: Number of days before and after today to check.
    :type days: int
    :param course: Optional course name used to filter assignments.
    :type course: str | None
    """
    await interaction.response.defer(ephemeral=True)

    api_key = await client.db.get_api_key(interaction.user.id)

    if not api_key:
        await interaction.followup.send(
            "You haven't linked your Canvas account yet. Use /link to get started.",
            ephemeral=True,
        )
        return

    headers = {"Authorization": f"Bearer {api_key}"}
    courses_url = "https://canvas.ou.edu/api/v1/courses"
    courses_params: dict[str, str] = {
        "per_page": "100",
        "enrollment_state": "active",
    }
    assignment_params: dict[str, str] = {
        "per_page": "100",
        "include[]": "submission",
    }

    try:
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=days)
        end_date = now + timedelta(days=days)

        results: list[tuple[datetime, str, str, str, str]] = []

        async with httpx.AsyncClient() as http_client:
            courses_response = await http_client.get(
                courses_url, headers=headers, params=courses_params
            )
            courses_response.raise_for_status()

            for canvas_course in courses_response.json():
                course_name = canvas_course.get("name") or canvas_course.get(
                    "course_code", "Unnamed Course"
                )

                # If the user selected a course, only check matching courses
                if course and course.lower() not in course_name.lower():
                    continue

                assignments_response = await http_client.get(
                    f"{courses_url}/{canvas_course.get('id')}/assignments",
                    headers=headers,
                    params=assignment_params,
                )
                assignments_response.raise_for_status()

                for assignment in assignments_response.json():
                    due_at = assignment.get("due_at")

                    if not due_at:
                        continue

                    due_date = datetime.fromisoformat(due_at.replace("Z", "+00:00"))

                    if not (start_date <= due_date <= end_date):
                        continue

                    submission = assignment.get("submission") or {}
                    submitted_at = submission.get("submitted_at")

                    submitted_date: Optional[datetime] = None
                    if submitted_at:
                        submitted_date = datetime.fromisoformat(
                            submitted_at.replace("Z", "+00:00")
                        )

                    status = submission_status(
                        {"due": due_date, "submitted_at": submitted_date}
                    )

                    if status == "submitted":
                        label = "Submitted"
                    elif status == "late":
                        label = "Submitted late"
                    elif due_date < now:
                        label = "Missing (past due)"
                    else:
                        label = "Not submitted yet"

                    results.append(
                        (
                            due_date,
                            assignment.get("name", "Unnamed Assignment"),
                            course_name,
                            label,
                            assignment.get("html_url"),
                        )
                    )

        results.sort(key=lambda item: item[0])

        if not results:
            await interaction.followup.send(
                f"No assignments due within {days} days of today.",
                ephemeral=True,
            )
            return

        message_lines = [f"**Submission status - {days} days before and after today**\n"]

        for due_date, name, course_name, label, assignment_url in results:
            timestamp = int(due_date.timestamp())

            message_lines.append(
                f"**{name}**\n"
                f"Course: `{course_name}`\n"
                f"Due: <t:{timestamp}:F> (<t:{timestamp}:R>)\n"
                f"Status: **{label}**\n"
                f"[Open in Canvas]({assignment_url})"
            )

        await interaction.followup.send("\n\n".join(message_lines), ephemeral=True)

    except httpx.HTTPStatusError as e:
        await interaction.followup.send(
            f"Failed to retrieve submissions. "
            f"Canvas API returned error status: {e.response.status_code}",
            ephemeral=True,
        )

    except Exception as e:
        print(f"Submissions error: {e}")

        await interaction.followup.send(
            "An unexpected error occurred while retrieving submissions.",
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
    params: dict[str, str] = {
    "per_page": "100",
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

sub_missions.autocomplete("course")(assignments_course_autocomplete)

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


class PerformanceMonitor:
    """
    Watch for errors then alert the host by email when one happens,
    being careful not to spam them with repeated alerts from the same source.

    :param host_email: Address that receives the alerts.
    :type host_email: str
    :param send_email: Function that sends an email, called as send_email(to, body).
    :type send_email: Callable[[str, str], None]
    :param alert_cooldown: Seconds before another email is sent for the same source.
    :type alert_cooldown: float
    """

    def __init__(
        self,
        host_email: str,
        send_email: Callable[[str, str], None],
        alert_cooldown: float = 600,
    ) -> None:
        self.host_email = host_email
        self.send_email = send_email
        self.alert_cooldown = alert_cooldown
        self.error_count = 0
        self.log: list[str] = []
        self._last_alert: dict[str, float] = {}

    def send_error_announcement(
        self, error: Exception, source: str, now: float | None = None
    ) -> bool:
        """
        Log an error and email the host unless the source is in its cooldown.

        A failed email is logged instead of raised, so the bot keeps running,
        and it does not start the cooldown, so the next error tries again.

        :param error: The exception that occurred.
        :type error: Exception
        :param source: Where it happened, e.g. a command name like "/courses".
        :type source: str
        :param now: Current time as a Unix timestamp (defaults to the real time).
        :type now: float | None
        :return: True if an email was sent, False otherwise.
        :rtype: bool
        """
        if now is None:
            now = datetime.now(timezone.utc).timestamp()

        self.error_count += 1
        when = datetime.fromtimestamp(now, timezone.utc).isoformat()
        details = f"{type(error).__name__} in {source} at {when}: {error}"

        last_alert = self._last_alert.get(source)
        if last_alert is not None and now - last_alert < self.alert_cooldown:
            self.log.append(f"SUPPRESSED {details}")
            return False

        try:
            self.send_email(self.host_email, f"NudgeBot error\n\n{details}")
        except Exception as e:
            self.log.append(f"EMAIL FAILED ({type(e).__name__}) {details}")
            return False

        self._last_alert[source] = now
        self.log.append(f"SENT {details}")
        return True