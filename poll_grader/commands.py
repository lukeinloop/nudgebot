"""
/poll command: a timed Discord poll that gives participants points in Canvas.

To turn it on, add this to bot/bot.py after the client is created:

    from poll_grader.commands import setup_poll
    setup_poll(client)
"""

import asyncio
from typing import Any

import discord
from discord import app_commands

from poll_grader.canvas_client import get_canvas_user_id, post_grade
from poll_grader.poll import MAX_MINUTES, Poll
from poll_grader.poll_grader import award_poll_points_async, get_links


class PollView(discord.ui.View):
    def __init__(self, poll: Poll) -> None:
        # the poll closes on its own timer, so the view never times out
        super().__init__(timeout=None)
        self.poll = poll

    @discord.ui.button(label="Participate", style=discord.ButtonStyle.primary)
    async def participate(
        self, interaction: discord.Interaction, button: discord.ui.Button[Any]
    ) -> None:
        result = self.poll.add_response(interaction.user.id)

        if result == "recorded":
            message = "You're in! Points get posted to Canvas when the poll closes."
        elif result == "duplicate":
            message = "You already participated."
        else:
            message = "Sorry, this poll is closed."

        await interaction.response.send_message(message, ephemeral=True)


def setup_poll(client: Any) -> None:
    """Add the /poll command to the bot."""

    @client.tree.command(
        name="poll", description="Start a timed poll that gives participants Canvas points"
    )
    @app_commands.describe(
        question="The question to ask",
        minutes=f"How long the poll is open (1-{MAX_MINUTES})",
        points="Points each participant gets",
        course_id="Canvas course ID (from /courses)",
        assignment_id="Canvas assignment ID to put the points in",
    )
    @app_commands.default_permissions(manage_guild=True)
    async def poll(
        interaction: discord.Interaction,
        question: str,
        minutes: app_commands.Range[int, 1, MAX_MINUTES],
        points: app_commands.Range[float, 0.1, 1000.0],
        course_id: str,
        assignment_id: str,
    ) -> None:
        api_key = await client.db.get_api_key(interaction.user.id)
        if not api_key:
            await interaction.response.send_message(
                "You haven't linked your Canvas account yet. Use /link to get started.",
                ephemeral=True,
            )
            return

        channel = interaction.channel
        if channel is None or not hasattr(channel, "send"):
            await interaction.response.send_message(
                "I can't post in this channel.", ephemeral=True
            )
            return

        try:
            new_poll = Poll.create(question, minutes, points, course_id, assignment_id)
        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)
            return

        view = PollView(new_poll)
        await interaction.response.send_message(
            f"**{new_poll.question}**\n"
            f"Press the button to participate for {new_poll.points:g} point(s). "
            f"Closes in {minutes} minute(s).",
            view=view,
        )
        poll_message = await interaction.original_response()

        # sleep can wake up a tiny bit early, so keep checking until it's closed
        while not new_poll.is_closed():
            await asyncio.sleep(max(0.5, new_poll.seconds_left()))

        await close_poll(client, channel, poll_message.id, view, new_poll, api_key)


async def close_poll(
    client: Any, channel: Any, message_id: int, view: PollView, poll: Poll, api_key: str
) -> None:
    """Disable the button, post the grades to Canvas, and send a summary."""
    for item in view.children:
        if isinstance(item, discord.ui.Button):
            item.disabled = True

    # interaction tokens expire after 15 minutes, so edit through the channel instead
    try:
        poll_message = await channel.fetch_message(message_id)
        await poll_message.edit(view=view)
    except discord.HTTPException:
        pass  # the button staying clickable isn't a big deal, it says "closed" anyway

    links = await get_links(poll.responders, client.db.get_api_key, get_canvas_user_id)

    async def post(student_id: Any, assignment_id: str, points: float) -> None:
        await post_grade(api_key, poll.course_id, assignment_id, student_id, points)

    result = await award_poll_points_async(poll.to_dict(), poll.assignment_id, links, post)

    lines = [
        f"**Poll closed:** {poll.question}",
        f"{len(result['awarded'])} of {len(poll.responders)} participant(s) "
        f"got {poll.points:g} point(s) in Canvas.",
    ]
    if result["skipped"]:
        mentions = ", ".join(f"<@{i}>" for i in result["skipped"])
        lines.append(f"Not linked to Canvas (use /link): {mentions}")
    if result["failed"]:
        mentions = ", ".join(f"<@{i}>" for i in result["failed"])
        lines.append(f"Canvas error, add these manually: {mentions}")

    # list people without pinging them
    await channel.send("\n".join(lines), allowed_mentions=discord.AllowedMentions.none())
