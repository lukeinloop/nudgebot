# TODO: insert standard file header / license / whatever

import aiosqlite
import time


# TODO: documentation
class DBHandler:
    # TODO: maybe it should have a password or something stored in the .env?
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def connect(self):
        self.db = await aiosqlite.connect(self.db_path)

    async def initialize_db(self):
        """Initialize the database with tables defined in the database schema.
        Note: in the future we might need to consider more robust backend solutions with proper backups, migrations, etc.
        """

        # Discord information
        await self.db.execute(
            "CREATE TABLE IF NOT EXISTS users ("
            "user_id INTEGER PRIMARY KEY,"  # internal ID for each user
            "discord_id VARCHAR(20) UNIQUE NOT NULL,"  # discord snowflake ID
            "canvas_user_id INTEGER UNIQUE,"  # canvas user ID
            "display_name VARCHAR(100),"  # cached from Discord
            "created_at TIMESTAMP"
            ")"
        )

        # Canvas credentials
        await self.db.execute(
            "CREATE TABLE IF NOT EXISTS canvas_credentials ("
            "credential_id INTEGER PRIMARY KEY,"
            "user_id INTEGER,"
            "canvas_base_url VARCHAR(255) NOT NULL,"  # institution's canvas domain
            "auth_type VARCHAR(20) NOT NULL,"  # should be either 'personal_token' or 'oauth2' TODO can we find a way to enum this or something
            "access_token TEXT NOT NULL,"
            "refresh_token TEXT,"  # null if using personal token
            "token_expires_at TIMESTAMP,"  # null if using nonexpiring personal token
            "linked_at TIMESTAMP,"
            "FOREIGN KEY(user_id) REFERENCES users(user_id)"
            ")"
        )

        # Canvas courses
        await self.db.execute(
            "CREATE TABLE IF NOT EXISTS courses ("
            "course_id INTEGER PRIMARY KEY,"  # matches Canvas' course ID
            "course_name VARCHAR(255) NOT NULL,"
            "course_code VARCHAR(50),"
            "term VARCHAR(50),"  # ex Sp2025, Fa 2023
            "last_synced_at TIMESTAMP"
            ")"
        )

        # Enrollments, a join table linking users to courses. Need to ensure users aren't in here for duplicate courses
        await self.db.execute(
            "CREATE TABLE IF NOT EXISTS enrollments ("
            "enrollment_id INTEGER PRIMARY KEY,"
            "user_id INTEGER,"
            "course_id INTEGER,"
            "role VARCHAR(30) NOT NULL,"  # 'student' 'teacher' 'TA' etc.
            "discord_server_id VARCHAR(20),"  # which discord server this applies to
            "FOREIGN KEY(user_id) REFERENCES users(user_id),"
            "FOREIGN KEY(course_id) REFERENCES courses(course_id)"
            ")"
        )

        # Assignment cache
        await self.db.execute(
            "CREATE TABLE IF NOT EXISTS assignments ("
            "assignment_id INTEGER PRIMARY KEY,"  # matches Canvas' assignment ID
            "course_id INTEGER,"
            "title VARCHAR(255) NOT NULL,"
            "description TEXT,"  # need to limit this so it doesn't get too large?
            "due_at TIMESTAMP,"  # base due date, may be null if overridden
            "has_overrides BOOLEAN,"  # whether to check assignment_due_overrides
            "updated_at TIMESTAMP,"  # Canvas's last-modified timestamp, not the table's updated_at timestamp
            "FOREIGN KEY(course_id) REFERENCES courses(course_id)"
            ")"
        )

        # Due-date overrides
        await self.db.execute(
            "CREATE TABLE IF NOT EXISTS assignment_due_overrides ("
            "override_id INTEGER PRIMARY KEY,"
            "assignment_id INTEGER,"
            "user_id INTEGER NULLABLE,"
            "due_at TIMESTAMP NOT NULL,"
            "FOREIGN KEY(assignment_id) REFERENCES assignments(assignment_id),"
            "FOREIGN KEY(user_id) REFERENCES users(user_id)"
            ")"
        )

        # Keep track of reminders already sent
        await self.db.execute(
            "CREATE TABLE IF NOT EXISTS reminders ("
            "reminder_id INTEGER PRIMARY KEY,"
            "user_id INTEGER,"
            "assignment_id INTEGER,"
            "remind_at TIMESTAMP NOT NULL,"
            "sent BOOLEAN DEFAULT FALSE,"
            "sent_at TIMESTAMP,"  # null until actually sent
            "FOREIGN KEY(assignment_id) REFERENCES assignments(assignment_id),"
            "FOREIGN KEY(user_id) REFERENCES users(user_id)"
            ")"
        )

    # Checks the "users" table for the given discord user ID
    async def has_api_key(self, discord_id: int) -> bool:
        cursor = await self.db.execute(
            f"SELECT * FROM users WHERE discord_id EQUALS {discord_id}"
        )

        return cursor.fetchall() == 0

    async def add_api_key(self, user_id: int, token: str):
        # TODO do we need to check if it already exists? for now just replace it anyways.
        await self.db.execute("UPDATE users SET ")

    async def create_user(self, discord_id: int, display_name: str):
        # TODO maybe we do INSERT OR REPLACE or something instead?
        await self.db.execute(
            f"INSERT INTO users VALUES({discord_id}, NULL, {display_name}, {time.time()})"
        )

        # TODO: need to also create a row for them in the canvas table
