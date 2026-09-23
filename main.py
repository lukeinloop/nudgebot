# TODO: insert standard file header and docstrings

import asyncio

from discord import Object

import os
from dotenv import load_dotenv

from bot.bot import client

from database.backend import DBHandler


def main():
    # automatically grab environment variables from a .env file in the same folder
    load_dotenv()

    # initialize DB
    db = DBHandler(os.environ["DB_PATH"])
    asyncio.run(db.connect())
    asyncio.run(db.initialize_db())

    # initialize bot (after DB so it is guaranteed to be loaded)
    client.guild_id = Object(os.environ["GUILD_ID"])
    client.db = db

    client.run(os.environ["TOKEN"])


if __name__ == "__main__":
    main()
