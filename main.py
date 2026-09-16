# TODO: insert standard file header and docstrings

import os
from dotenv import load_dotenv

from bot.bot import client


def main():
    # automatically grab environment variables from a .env file in the same folder
    load_dotenv()

    client.run(os.environ["TOKEN"])


if __name__ == "__main__":
    # TODO: have some sort of auto-restart / reconnect feature?
    # or we can handle that via command line script or systemctl process

    main()
