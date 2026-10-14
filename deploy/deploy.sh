#!/bin/bash
# Pull-based CD: runs every 2 minutes from nudge-bot-deploy.timer.
# Deploys origin/main if it has new commits, then verifies the bot came back up.

set -euo pipefail

APP_DIR="/home/dietpi/nudgebot"
VENV="$APP_DIR/.venv"
BRANCH="main"
SERVICE="nudge-bot"

cd "$APP_DIR"

echo "Checking GitHub for updates..."

git fetch origin "$BRANCH"

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse "origin/$BRANCH")

if [ "$LOCAL" = "$REMOTE" ]; then
    echo "Already up to date."
    exit 0
fi

echo "New version detected."
echo "Local:  $LOCAL"
echo "Remote: $REMOTE"

git pull --ff-only origin "$BRANCH"

# If anything below fails, roll the checkout back so the next timer run
# retries the deploy instead of seeing "Already up to date" on a half-deployed app.
rollback() {
    echo "Deployment failed; rolling back to $LOCAL" >&2
    git reset --hard "$LOCAL"
}
trap rollback ERR

echo "Installing dependencies..."

"$VENV/bin/python" -m pip install --quiet -r "$APP_DIR/requirements.txt"

echo "Restarting NudgeBot..."

sudo systemctl restart "$SERVICE"

# Health check: the service must still be running a few seconds after restart.
sleep 5
if ! systemctl is-active --quiet "$SERVICE"; then
    echo "$SERVICE is not running after restart" >&2
    false
fi

trap - ERR
echo "Deployment complete! Now running $(git rev-parse --short HEAD)"
