# Poll to Canvas Grade

`/poll` starts a timed poll in Discord. Everyone who presses **Participate** before
it closes gets points (or extra credit) added to a Canvas assignment.

## Usage

`/poll question minutes points course_id assignment_id`

- Only people with *Manage Server* can run it, and they need a teacher/TA Canvas token linked with `/link`.
- Students need to `/link` their own Canvas account to get points. Anyone who isn't linked is listed when the poll closes.
- Get the course ID from `/courses`. The assignment ID is in the assignment's Canvas URL.
- Polls are stored in memory, so restarting the bot cancels any open polls.

## Turning it on

Add this to `bot/bot.py` after the client is created:

```python
from poll_grader.commands import setup_poll
setup_poll(client)
```

## Files

| File | What it does |
|------|--------------|
| `poll.py` | `Poll` class: timer, one response per person, rejects late responses |
| `poll_grader.py` | Checks the poll and figures out who gets points |
| `canvas_client.py` | Posts grades to Canvas and looks up Canvas user IDs |
| `commands.py` | The `/poll` command and the Participate button |

## Running the unit tests

```
git clone https://github.com/lukeinloop/nudgebot.git
cd nudgebot
pip install -r requirements.txt
python -m unittest discover -p "poll_grader_test.py" -v test
```

Run all the poll tests with `python -m unittest discover -p "poll*_test.py" -v test`.
The tests use mocks, so they don't need a Discord token, a Canvas token, or internet.
