# CI/CD Code Review Session – Midterm Alternative (15 min)

Feature: CI/CD pipeline for NudgeBot (GitHub Actions CI + pull-based systemd CD).

## Checklist
- [ ] Editor open on the repo; GitHub Actions tab open; Discord open with the bot online
- [ ] SSH session to the host running `journalctl -fu nudge-bot-deploy` (optional, shows the deploy live)
- [ ] Branch protection on `main` requires the "Unit Tests" check
- [ ] A small safe change picked for the live demo (below)

## 1. Setup & Context (2 min)
- NudgeBot: Discord bot that pulls Canvas courses/assignments (`/courses`, `/assignments`).
- Pipeline goal: no untested code reaches `main`, and `main` deploys itself.

## 2. Live Code Review (5 min)
- `.github/workflows/unit-tests.yml`: triggers (PR + push to `main`), Python 3.14, pip cache, `mypy` strict flags, `unittest discover`.
- Branching/merge flow (README "Development"): `feat/<name>` or `bug/<name>` → PR → CI green → review → merge.
- `deploy/deploy.sh` + `nudge-bot-deploy.timer` (every 2 min) + `nudge-bot.service`: fetch, fast-forward, install deps, restart, health check, rollback on failure.
- Why pull-based: the host sits behind a home/campus network, so GitHub can't push to it; polling needs no open ports or stored SSH keys.
- Key commits to show: workflow added, deploy scripts added, deploy.sh `-m pip` fix + rollback/health check.

## 3. Live Modification & Deployment (5 min)
1. `git switch -c feat/demo-change`
2. Small change: add `hours_late()` to `submission_status.py` plus two tests in `test/submission_status_test.py`.
   Prepared in `docs/live_demo_change.patch`; apply with `git apply docs/live_demo_change.patch`
   (or type it in by hand during the demo). It reports how many hours past the deadline a submission was.
3. Commit, push, open PR to `main`: show CI running mypy + tests (optionally break a test first to show it blocking, then fix).
4. Merge once green.
5. Show the host picking it up within ~2 min (`journalctl -u nudge-bot-deploy`) and the new behavior in Discord.

## 4. Q&A (3 min) – likely questions
- What happens if tests fail? PR can't merge (branch protection); nothing deploys.
- What if the deploy fails halfway? ERR trap resets the checkout so the next timer run retries.
- Why `--ff-only`? Never creates merge commits or overwrites local state on the host.
- Limitations: polling delay up to 2 min; deploy isn't tied to the CI result except via branch protection; no staging environment.
