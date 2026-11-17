"""
NudgeBot: Canvas Integration / Discord Bot

Originally written for the CS-3203 Software Engineering class at the University of Oklahoma in Fall 2026.

Copyright 2026 Group K: Luke Sewell, Janes Le, Daniel Brown. Not open source. All rights reserved.
"""

"""
Database access and initialization utilities for NudgeBot.

This module provides the :class:`DBHandler` class which manages the
SQLite database used by NudgeBot. It is responsible for establishing
the database connection, creating the required tables, and performing
user and Canvas credential operations.
"""

from pony.orm import Database, db_session
from models import *
from time import time
from sys import maxsize

# from cryptography.fernet import Fernet
#
# def encryption():
#     # look for existing encryption key
#     self.encryption_key: bytes
#     try:
#         with open(key_path, "rb") as key:
#             self.encryption_key = key.read()
#     # if there is no existing key, make a new one
#     except FileNotFoundError as e:
#         print("Existing encryption key not found, generating new one...")
#         with open(key_path, "wb") as key:
#             new_key = Fernet.generate_key()
#             key.write(new_key)

#             self.encryption_key = new_key


class BackendConnection:
    """
    TODO REWRITE

    The :class:`BackendConnection` class provides an asynchronous interface for
    connecting to and interacting with the database.

    :param db_path: Path to the database file.
    :type db_path: str
    """

    def __init__(self, db: Database, key_path: str):
        """
        Initialize database handler.

        TODO REWRITE

        :param db_path: Path to the database file.
        :type db_path: str
        :param key_path: Path to the key file used for encryption.
        :type key_path: str
        """

        self.db = db
        # TODO any other init?
        # need to self.db.bind()
        # maybe self.db.connect() too


    # TODO
    def add_api_key(self, discord_id: int, canvas_base_url: str, token: str) -> None:
        """
        Store a Canvas API token for a Discord user.

        First looks up the internal database user ID associated
        with the given Discord ID. If the user exists, their Canvas
        credentials are inserted into the canvas_credentials table.

        :param discord_id: Discord snowflake ID of the user.
        :type discord_id: int
        :param canvas_base_url: Base URL of the user's Canvas instance.
        :type canvas_base_url: str
        :param token: Canvas personal access token.
        :type token: str
        """
        pass
        # TODO


    @db_session
    def create_user(self, discord_id: int) -> InternalUser | None:
        """
        Create a new Discord user in the database.

        :param discord_id: Discord snowflake ID of the user.
        :type discord_id: int
        :return: the InternalUser model that was created
        :rtype: InternalUser
        """
        user = InternalUser(discord_id=discord_id)

        self.db.commit()

        return user


    @db_session
    def create_canvas_user(
        self, discord_id: int, canvas_id: int, access_token: str
    ) -> CanvasUser | None:
        
        #TODO: docstring
        
        internal_user = InternalUser.get(discord_id=discord_id)

        # input validation
        if not (0 < canvas_id < maxsize):
            #TODO: throw an error?
            return None
        elif not (50 < len(access_token) < 80):
            #TODO: throw an error?
            return None

        # actually make the entry
        canvas_user = CanvasUser(
            discord_id=internal_user.discord_id,
            canvas_id=canvas_id,
            access_token=access_token,
            linked_at=time(),
        )

        self.db.commit()

        return canvas_user


    @db_session
    def update_canvas_user(self, **kwargs) -> CanvasUser | None:
        #TODO: docstring
        canvas_user: CanvasUser

        if "discord_id" in kwargs:
            canvas_user = CanvasUser.get(discord_id=kwargs["discord_id"])
        elif "canvas_id" in kwargs:
            canvas_user = CanvasUser.get(canvas_id=kwargs["canvas_id"])
        else:
            return None

        #TODO: input validation
        #TODO: update the information

        self.db.commit()

        return canvas_user


    # courses
    @db_session
    def create_canvas_course(self, course_id: int, name: str, code: str, term: int) -> CanvasCourse | None:
        #TODO docstring

        # input validation
        # check that the name is within bounds
        if not (1 < len(name) < 100):
            #TODO ??? what do we do here?
            return None
        # check that the code is reasonable
        #TODO

        # check that the term is reasonable
        #TODO

        course = CanvasCourse(course_id=course_id, name=name, code=code, term=term)

        self.db.commit()

        return course