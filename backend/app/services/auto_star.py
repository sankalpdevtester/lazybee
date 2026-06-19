"""
Auto-star: Shivaani-spec, PirateKingLuffie, liveinsaaninsaan all star sankalpdevtester repos.
Stars with small random delays between each repo to look organic.
"""
import os
import time
import random
from github import Github, Auth, GithubException

AUTOMATION_USER = "sankalpdevtester"

def _get_star_tokens() -> list[str]:
    tokens = [
        os.getenv("SHIVAANI_TOKEN", "").strip(),
        os.getenv("PIRATE_TOKEN", "").strip(),
        os.getenv("LIVE_TOKEN", "").strip(),
        # Main account can't star its own repos — skip SANKALPDEVTESTER_TOKEN
    ]
    return [t for t in tokens if t]


def star_all_repos():
    from app.storage import append_log
    from datetime import datetime

    def log(msg, level="info"):
        append_log(datetime.utcnow().isoformat(), "stars", msg, level)

    main_token = os.getenv("SANKALPDEVTESTER_TOKEN", "").strip()
    if not main_token:
        log("No SANKALPDEVTESTER_TOKEN — cannot list repos", "error")
        return

    try:
        main_g = Github(auth=Auth.Token(main_token))
        main_user = main_g.get_user(AUTOMATION_USER)
        repos = [r for r in main_user.get_repos(type="public") if not r.private]
        log(f"Found {len(repos)} public repos")
    except Exception as e:
        log(f"Failed to fetch repos: {e}", "error")
        return

    tokens = _get_star_tokens()
    if not tokens:
        log("No side-account tokens set (SHIVAANI_TOKEN, PIRATE_TOKEN, LIVE_TOKEN)", "error")
        return

    total_starred = 0
    for token in tokens:
        try:
            g = Github(auth=Auth.Token(token))
            star_user = g.get_user()
            username = star_user.login

            # Get current starred set
            already_starred = {r.full_name for r in star_user.get_starred()}

            count = 0
            for repo in repos:
                if repo.full_name not in already_starred:
                    try:
                        star_user.add_to_starred(repo)
                        count += 1
                        total_starred += 1
                        # Small delay between stars — looks organic, avoids rate limit
                        time.sleep(random.uniform(1.5, 4.0))
                    except GithubException as e:
                        if e.status == 429:
                            log(f"{username}: rate limited, waiting 60s", "error")
                            time.sleep(60)
                        # else skip silently
                    except Exception:
                        pass

            log(f"{username} starred {count} new repos")
        except Exception as e:
            log(f"Star failed for a side account: {e}", "error")

    log(f"Auto-star complete — {total_starred} new stars across all accounts")


if __name__ == "__main__":
    star_all_repos()
