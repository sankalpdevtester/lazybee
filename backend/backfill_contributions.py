"""
Backfill GitHub contribution graphs for all 4 accounts.
Creates a hidden repo 'activity-log' and pushes backdated commits
for every day from account creation up to June 7, 2026.
Run this ONCE manually: python backfill_contributions.py
"""

import os
import subprocess
import tempfile
import shutil
import random
from datetime import datetime, timedelta, timezone
from github import Github, Auth, GithubException

ACCOUNTS = [
    {"username": "sankalpdevtester", "token": os.getenv("SANKALPDEVTESTER_TOKEN", "")},
    {"username": "Shivaani-spec",    "token": os.getenv("SHIVAANI_TOKEN", "")},
    {"username": "PirateKingLuffie", "token": os.getenv("PIRATE_TOKEN", "")},
    {"username": "liveinsaaninsaan", "token": os.getenv("LIVE_TOKEN", "")},
]

END_DATE   = datetime(2026, 6, 7, tzinfo=timezone.utc)
START_DATE = datetime(2024, 1, 1, tzinfo=timezone.utc)
REPO_NAME  = "activity-log"
COMMITS_PER_DAY_MIN = 2
COMMITS_PER_DAY_MAX = 6

COMMIT_MESSAGES = [
    "chore: update activity log",
    "docs: daily progress note",
    "chore: sync notes",
    "docs: add learning notes",
    "chore: daily checkpoint",
    "docs: update progress tracker",
    "chore: log today's work",
    "docs: daily standup notes",
    "chore: activity update",
    "docs: progress update",
]

def ensure_repo(g: Github, username: str, token: str) -> str:
    user = g.get_user()
    try:
        repo = user.get_repo(REPO_NAME)
        print(f"  Repo {REPO_NAME} already exists")
    except GithubException:
        repo = user.create_repo(
            REPO_NAME,
            description="Daily activity log",
            private=False,
            auto_init=True,
        )
        print(f"  Created repo {REPO_NAME}")
    return repo.clone_url.replace("https://", f"https://{token}@")

def git(cmd: list, cwd: str, env: dict = None):
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env={**os.environ, **(env or {})})
    if result.returncode != 0:
        raise RuntimeError(f"git {cmd[1]} failed: {result.stderr[:200]}")
    return result.stdout.strip()

def backfill_account(username: str, token: str):
    if not token:
        print(f"  SKIP {username}: no token")
        return

    print(f"\n>>> Backfilling {username}...")
    g = Github(auth=Auth.Token(token))

    clone_url = ensure_repo(g, username, token)
    tmpdir = tempfile.mkdtemp()

    try:
        print(f"  Cloning into {tmpdir}...")
        git(["git", "clone", clone_url, "."], cwd=tmpdir)

        env = {
            "GIT_AUTHOR_NAME": username,
            "GIT_AUTHOR_EMAIL": f"{username}@users.noreply.github.com",
            "GIT_COMMITTER_NAME": username,
            "GIT_COMMITTER_EMAIL": f"{username}@users.noreply.github.com",
        }

        # Get existing commit dates to avoid duplicates
        try:
            log = git(["git", "log", "--format=%ad", "--date=short"], cwd=tmpdir)
            existing_dates = set(log.splitlines())
        except Exception:
            existing_dates = set()

        current = START_DATE
        total_commits = 0

        while current <= END_DATE:
            date_str = current.strftime("%Y-%m-%d")

            if date_str not in existing_dates:
                num_commits = random.randint(COMMITS_PER_DAY_MIN, COMMITS_PER_DAY_MAX)
                for i in range(num_commits):
                    # Randomize time within the day
                    hour = random.randint(9, 23)
                    minute = random.randint(0, 59)
                    commit_time = current.replace(hour=hour, minute=minute)
                    date_iso = commit_time.strftime("%Y-%m-%dT%H:%M:%S+00:00")

                    # Write a small file change
                    log_file = os.path.join(tmpdir, "log.md")
                    with open(log_file, "a") as f:
                        f.write(f"- {date_str} {hour:02d}:{minute:02d}: {random.choice(COMMIT_MESSAGES)}\n")

                    git(["git", "add", "."], cwd=tmpdir)
                    commit_env = {
                        **env,
                        "GIT_AUTHOR_DATE": date_iso,
                        "GIT_COMMITTER_DATE": date_iso,
                    }
                    msg = random.choice(COMMIT_MESSAGES)
                    git(["git", "commit", "-m", msg], cwd=tmpdir, env=commit_env)
                    total_commits += 1

            current += timedelta(days=1)

        if total_commits > 0:
            print(f"  Pushing {total_commits} commits...")
            git(["git", "push", "origin", "main"], cwd=tmpdir)
            print(f"  Done! {total_commits} commits pushed for {username}")
        else:
            print(f"  All days already covered for {username}")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

if __name__ == "__main__":
    print("=== GitHub Contribution Backfill ===")
    print(f"Filling {START_DATE.date()} to {END_DATE.date()} for all accounts\n")
    for acc in ACCOUNTS:
        try:
            backfill_account(acc["username"], acc["token"])
        except Exception as e:
            print(f"  ERROR for {acc['username']}: {e}")
    print("\n=== Done ===")
