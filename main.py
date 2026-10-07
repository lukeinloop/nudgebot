"""
NudgeBot: Canvas Integration / Discord Bot

Originally written for the CS-3203 Software Engineering class at the University of Oklahoma in Fall 2026.

Copyright 2026 Group K: Luke Sewell, Janes Le, Daniel Brown. Not open source. All rights reserved.
"""

"""
Entry point for NudgeBot.

This module loads environment variables, initializes the database,
configures NudgeBot, and starts NudgeBot
"""

import asyncio
import os

from dotenv import load_dotenv
from discord import Object

from bot.bot import client
from database.backend import DBHandler


def main() -> None:
    """
    Initialize the database and start NudgeBot.

    Environment variables are loaded from a .env file. The database
    connection and schema are initialized before the NudgeBot is
    started to make sure that the database is ready when the bot begins
    to start handling events and commands.
    """

    # automatically grab environment variables from a .env file in the same folder
    load_dotenv()

    # initialize DB
    db = DBHandler(os.environ["DB_PATH"], os.environ["KEY_PATH"])
    asyncio.run(db.connect())
    asyncio.run(db.initialize_db())

    # initialize bot (after DB so it is guaranteed to be loaded)
    client.guild_id = Object(os.environ["GUILD_ID"])
    client.db = db

    # start the bot
    client.run(os.environ["TOKEN"])


if __name__ == "__main__":
    main()
