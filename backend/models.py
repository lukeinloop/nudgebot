from datetime import datetime
from time import time

from pony.orm import Database, Required, Optional, PrimaryKey

db = Database()

# TODO: https://stackoverflow.com/questions/14461851/how-to-have-an-automatic-timestamp-in-sqlite


class InternalUser(db.Entity):
    """Internal user model, linking Discord and Canvas IDs."""

    # discord snowflake ID of the user
    discord_id = Required(int, unique=True)
    # canvas user ID (NULL until canvas account linked), from CanvasUser table
    canvas_id = Optional("CanvasUser")

    updated_at = Required(datetime, default=time)


class CanvasUser(db.Entity):
    """Canvas user model, stores Canvas access token."""

    # canvas user ID
    canvas_id = Required(int, unique=True, fk_name="discord_id")
    # canvas access token (generated from canvas settings page)
    access_token = Required(str, max_len=72)
    linked_at = Required(
        datetime
    )  # isn't this just when this entry is created? probably?

    updated_at = Required(datetime, default=time)


class CanvasCourse(db.Entity):
    """Canvas course model, see:
    https://developerdocs.instructure.com/services/canvas/resources/courses
    """

    # the unique identifier of the course, from Canvas
    course_id = PrimaryKey(int, auto=False)
    # name of the course, from Canvas
    name = Required(str, max_len=100)
    # course code (ex: CS3203), from Canvas
    code = Required(str, max_len=16)
    # TODO FIXME we might have to get this from the Term object, and then do some math to assign it to a human-readable semester
    term = Required(int)

    updated_at = Required(datetime, default=time)


class Role(db.Entity):
    """Internal constant model for roles used in the enrollments table."""

    role = Required(str, max_len=20)


class Enrollment(db.Entity):
    """Enrollments model, used to match internal users to courses, and discord server snowflakes."""

    # internal user ID (foreign key)
    user_id = Optional("InternalUser.id")
    # canvas course ID (foreign key)
    course_id = Optional("CanvasCourse")
    # a role from the Roles table (professor, student, TA, etc.)
    role = Required("Role")
    # discord server ID the command was run in
    discord_server_id = Required(int)  # TODO this almost belongs in a separate table?

    updated_at = Required(datetime, default=time)


class Assignment(db.Entity):
    """Assignment model for caching Canvas data."""

    # Canvas course ID, foreign key
    course_id = Required("CanvasCourse")
    # assignment title, from Canvas
    title = Required(str, max_len=255)
    # assignment description, from Canvas
    description = Optional(str, max_len=255)

    # when the assignment is due, as listed in Canvas
    due_at = Required(datetime)
    # optionally, when the reminder should be sent, if not the default based on when Canvas says it is due
    reminder_date = Optional(datetime)

    # the last time the assignment was modified in Canvas (i.e. so we can check for an updated due date)
    last_modified = Required(datetime)

    updated_at = Required(datetime, default=time)


class Reminder(db.Entity):
    """Reminder model to keep track of when reminders are due, and which have already been sent."""

    user_id = Required(int)  # TODO foreign key
    assignment_id = Required(int)  # TODO foreign key
    remind_at = Required(datetime)
    sent = Required(bool)
    sent_at = Required(datetime)

    updated_at = Required(datetime, default=time)
