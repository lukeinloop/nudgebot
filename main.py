# TODO: insert standard file header and docstrings

from discord import Object

import os
from dotenv import load_dotenv

from bot.bot import client

from database.backend import DBHandler


def main():
    # automatically grab environment variables from a .env file in the same folder
    load_dotenv()

    #FIXME
    db = DBHandler()

    # TODO: need to find a way to call sync_commands or something from here with the environment variables for the servers
    # the bot is in somehow

    client.guild_id = Object(os.environ["GUILD_ID"])
    client.db = db

    client.run(os.environ["TOKEN"])


if __name__ == "__main__":
    # TODO: have some sort of auto-restart / reconnect feature?
    # or we can handle that via command line script or systemctl process

    main()
