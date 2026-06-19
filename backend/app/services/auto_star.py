"""
Auto-star: Shivaani-spec, PirateKingLuffie, liveinsaaninsaan all star sankalpdevtester repos.
Run once to star existing repos, then runs daily to star new ones.
"""
import os
from github import Github, Auth, GithubException

AUTOMATION_USER = "sankalpdevtester"
STAR_ACCOUNTS = [
    os.getenv("SHIVAANI_TOKEN", ""),
    os.getenv("PIRATE_TOKEN", ""),
    os.getenv("LIVE_TOKEN", ""),
]

def star_all_repos():
    from app.storage import append_log
    from datetime import datetime
    def log(msg): append_log(datetime.utcnow().isoformat(), "stars", msg, "info")

    main_g = Github(auth=Auth.Token(os.getenv("SANKALPDEVTESTER_TOKEN", "")))
    main_user = main_g.get_user(AUTOMATION_USER)
    repos = list(main_user.get_repos(type="public"))
    log(f"Found {len(repos)} public repos to star")

    for token in STAR_ACCOUNTS:
        if not token:
            continue
        try:
            g = Github(auth=Auth.Token(token))
            star_user = g.get_user()
            already_starred = {r.full_name for r in star_user.get_starred()}
            starred_count = 0
            for repo in repos:
                if repo.full_name not in already_starred:
                    try:
                        star_user.add_to_starred(repo)
                        starred_count += 1
                    except GithubException:
                        pass
            log(f"{star_user.login} starred {starred_count} new repos")
        except Exception as e:
            log(f"Star failed for account: {e}", )

if __name__ == "__main__":
    star_all_repos()
