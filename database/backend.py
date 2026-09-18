# TODO: insert standard file header / license / whatever

import aiosqlite


class DBHandler:
    # TODO: maybe it should have a password or something stored in the .env?
    def __init__(self):
        pass

    def initialize_db(self):
        # TODO: create tables, etc.
        # ensure it doesn't already exist though
        pass

    def add_api_key(self, token: str):
        # TODO: check if it already exists
        # update if it does
        # create new user if it doesn't or something
        pass

    def create_user(self, user_id: int):
        pass  # TODO: create new entry or update exist entry
