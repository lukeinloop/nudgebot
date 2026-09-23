from datetime import datetime, timedelta

# TESTINGG

def assignment_due_soon(due_date):
    """
    Checks whether an assignment is due within the next 24 hours.
    """
    now = datetime.now()
    reminder_time = now + timedelta(hours=24)

    return now < due_date <= reminder_time


async def send_assignment_reminder(channel, assignment):
    """
    Sends an assignment reminder to a Discord channel.
    """
    assignment_name = assignment["name"]
    due_date = assignment["due_at"]

    await channel.send(
        f"📚 **Assignment Reminder**\n"
        f"{assignment_name} is due {due_date}!"
    )


async def check_assignments(channel, assignments):
    """
    Checks assignments and sends reminders for assignments due soon.
    """
    for assignment in assignments:
        due_date = assignment["due_at"]

        if assignment_due_soon(due_date):
            await send_assignment_reminder(channel, assignment)