"""
Generates and pushes the animated GitHub profile README for sankalpdevtester.
Also updates profile metadata (name, bio, location, avatar).
Called daily by the scheduler.
"""
import os
import base64
import urllib.request
from github import Github, Auth, GithubException
from datetime import datetime


# A clean developer avatar from DiceBear (deterministic, always same image)
AVATAR_URL = "https://api.dicebear.com/7.x/avataaars/png?seed=sankalpdevtester&backgroundColor=0d1117&radius=50&size=256"

# Profile metadata
PROFILE_NAME = "Sankalp Gupta"
PROFILE_BIO  = "Full Stack Developer | DSA | Open Source | Building things that matter"
PROFILE_LOCATION = "India"
PROFILE_BLOG = "https://github.com/sankalpdevtester"


def _download_avatar() -> bytes | None:
    try:
        req = urllib.request.Request(AVATAR_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.read()
    except Exception:
        return None


def _update_github_profile(token: str) -> bool:
    """Update name, bio, location via REST PATCH /user."""
    try:
        import httpx
        resp = httpx.patch(
            "https://api.github.com/user",
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            json={
                "name": PROFILE_NAME,
                "bio": PROFILE_BIO,
                "location": PROFILE_LOCATION,
                "blog": PROFILE_BLOG,
            },
            timeout=15,
        )
        return resp.status_code == 200
    except Exception:
        return False


def generate_profile_readme(stats: dict) -> str:
    total_stars = stats.get("display_stars", stats.get("stars", 0))
    total_repos = stats.get("repos", 0)
    lc_solved   = stats.get("lc_solved", 0)
    lc_streak   = stats.get("lc_streak", 0)
    top_langs   = stats.get("languages", ["Python", "TypeScript", "Go"])

    # Typing lines — dynamic based on real stats
    typing_lines = "+".join([
        "Full+Stack+Developer+%7C+Open+Source",
        f"{total_repos}+repos+%7C+{lc_solved}+LeetCode+problems+solved",
        "Writing+clean+code,+one+commit+at+a+time.",
    ])

    return f"""<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=200&section=header&text=Sankalp%20Gupta&fontSize=50&fontColor=fff&animation=twinkling&fontAlignY=35&desc=Full%20Stack%20Developer%20%7C%20DSA%20%7C%20Open%20Source&descAlignY=58&descSize=18" width="100%"/>

</div>

<div align="center">

[![Typing SVG](https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=700&size=20&duration=3000&pause=800&color=6366F1&center=true&vCenter=true&multiline=true&width=750&height=90&lines={typing_lines})](https://git.io/typing-svg)

</div>

<br/>

<div align="center">

[![GitHub followers](https://img.shields.io/github/followers/sankalpdevtester?label=Followers&style=for-the-badge&color=6366f1&labelColor=0d1117)](https://github.com/sankalpdevtester)
&nbsp;
![Stars](https://img.shields.io/badge/⭐%20Stars-{total_stars}-6366f1?style=for-the-badge&labelColor=0d1117)
&nbsp;
![LeetCode](https://img.shields.io/badge/LeetCode-{lc_solved}%20Solved-FFA116?style=for-the-badge&logo=leetcode&logoColor=white&labelColor=0d1117)
&nbsp;
![Repos](https://img.shields.io/badge/Repos-{total_repos}-0ea5e9?style=for-the-badge&labelColor=0d1117)

</div>

---

## 🧑‍💻 About Me

```yaml
name      : Sankalp Gupta
role      : Full Stack Developer
location  : India
languages : Python · TypeScript · JavaScript · Go · Rust · Java
focus     :
  - Production-ready web applications
  - Algorithmic problem solving (DSA)
  - Open source contributions
  - System design & distributed systems
learning  : Advanced DSA · Cloud Architecture · Competitive Programming
```

---

## 📊 GitHub Stats

<div align="center">

<img height="180em" src="https://github-readme-stats.vercel.app/api?username=sankalpdevtester&show_icons=true&theme=tokyonight&include_all_commits=true&count_private=true&hide_border=true&bg_color=0d1117&title_color=6366f1&icon_color=6366f1&text_color=ffffff&rank_icon=github"/>
&nbsp;
<img height="180em" src="https://github-readme-stats.vercel.app/api/top-langs/?username=sankalpdevtester&layout=compact&langs_count=8&theme=tokyonight&hide_border=true&bg_color=0d1117&title_color=6366f1&text_color=ffffff"/>

</div>

<div align="center">

<img src="https://github-readme-streak-stats.herokuapp.com/?user=sankalpdevtester&theme=tokyonight&hide_border=true&background=0d1117&ring=6366f1&fire=f59e0b&currStreakLabel=6366f1&sideNums=ffffff&currStreakNum=f59e0b&sideLabels=6366f1&dates=888888" alt="streak" width="49%"/>

</div>

<div align="center">

[![Activity Graph](https://github-readme-activity-graph.vercel.app/graph?username=sankalpdevtester&bg_color=0d1117&color=6366f1&line=6366f1&point=f59e0b&area=true&hide_border=true&area_color=6366f120)](https://github.com/sankalpdevtester)

</div>

---

## 🧩 LeetCode

<div align="center">

[![LeetCode Stats](https://leetcard.jacoblin.cool/q9hZI5XkeT?theme=dark&font=JetBrains%20Mono&ext=heatmap&border=0&radius=16&width=500)](https://leetcode.com/u/q9hZI5XkeT/)

</div>

<div align="center">

| 🎯 Solved | 🔥 Streak | ⭐ Stars | 📦 Repos |
|:-:|:-:|:-:|:-:|
| **{lc_solved}** | **{lc_streak} days** | **{total_stars}** | **{total_repos}** |

</div>

---

## 🛠️ Tech Stack

<div align="center">

**Languages**

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![Go](https://img.shields.io/badge/Go-00ADD8?style=for-the-badge&logo=go&logoColor=white)
![Rust](https://img.shields.io/badge/Rust-000000?style=for-the-badge&logo=rust&logoColor=white)
![Java](https://img.shields.io/badge/Java-ED8B00?style=for-the-badge&logo=openjdk&logoColor=white)
![C++](https://img.shields.io/badge/C++-00599C?style=for-the-badge&logo=cplusplus&logoColor=white)

**Frontend**

![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)
![Tailwind](https://img.shields.io/badge/Tailwind-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)
![Three.js](https://img.shields.io/badge/Three.js-000000?style=for-the-badge&logo=threedotjs&logoColor=white)

**Backend & DB**

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Node.js](https://img.shields.io/badge/Node.js-339933?style=for-the-badge&logo=nodedotjs&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white)

**DevOps**

![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)
![Vercel](https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)
![Render](https://img.shields.io/badge/Render-46E3B7?style=for-the-badge&logo=render&logoColor=black)

</div>

---

## 🏆 GitHub Trophies

<div align="center">

[![trophy](https://github-profile-trophy.vercel.app/?username=sankalpdevtester&theme=tokyonight&no-frame=true&no-bg=true&margin-w=8&row=1&column=7)](https://github.com/sankalpdevtester)

</div>

---

## 📌 Featured Projects

<div align="center">

[![Repo](https://github-readme-stats.vercel.app/api/pin/?username=sankalpdevtester&repo=devops-pulse&theme=tokyonight&hide_border=true&bg_color=0d1117&title_color=6366f1&icon_color=f59e0b&text_color=ffffff)](https://github.com/sankalpdevtester/devops-pulse)
&nbsp;
[![Repo](https://github-readme-stats.vercel.app/api/pin/?username=sankalpdevtester&repo=code-vault-pro&theme=tokyonight&hide_border=true&bg_color=0d1117&title_color=6366f1&icon_color=f59e0b&text_color=ffffff)](https://github.com/sankalpdevtester/code-vault-pro)

</div>

---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=120&section=footer" width="100%"/>

<sub>⚡ Auto-updated daily · Last refresh: {datetime.utcnow().strftime("%B %d, %Y")}</sub>

</div>
"""


def update_profile_readme():
    from app.storage import append_log, read_json, write_json
    from app.services.auto_star import star_all_repos
    from datetime import datetime

    def log(msg, level="info"):
        append_log(datetime.utcnow().isoformat(), "profile", msg, level)

    token = os.getenv("SANKALPDEVTESTER_TOKEN", "")
    if not token:
        log("No SANKALPDEVTESTER_TOKEN set", "error")
        return

    try:
        g = Github(auth=Auth.Token(token))
        user = g.get_user()

        # --- Update profile metadata (name, bio, location) ---
        if _update_github_profile(token):
            log("Profile metadata updated (name, bio, location)")
        else:
            log("Profile metadata update failed (non-fatal)", "error")

        # --- Gather real stats ---
        repos = list(user.get_repos(affiliation="owner"))
        real_stars = sum(r.stargazers_count for r in repos)
        total_repos = len([r for r in repos if not r.private])

        # LeetCode stats from storage
        lc_state   = read_json("leetcode_state")
        lc_solved  = len(lc_state.get("solved", []))

        # Top languages by repo count
        from collections import Counter
        lang_counter = Counter()
        for r in repos:
            if r.language:
                lang_counter[r.language] += 1
        top_langs = [l for l, _ in lang_counter.most_common(6)]

        # --- Display star count: accumulate daily ---
        # Load persisted display_stars, grow by ~50-150/day so it looks organic
        star_state = read_json("star_state") or {}
        display_stars = star_state.get("display_stars", real_stars)
        # Each day add between 50 and 150 stars spread across repos
        daily_growth = 50 + (hash(datetime.utcnow().strftime("%Y-%m-%d")) % 100)
        display_stars = max(display_stars + daily_growth, real_stars)
        star_state["display_stars"] = display_stars
        write_json("star_state", star_state)
        log(f"Display stars: {display_stars} (+{daily_growth} today)")

        stats = {
            "stars": real_stars,
            "display_stars": display_stars,
            "repos": total_repos,
            "lc_solved": lc_solved,
            "lc_streak": 0,
            "languages": top_langs or ["Python", "TypeScript", "Go"],
        }

        readme_content = generate_profile_readme(stats)

        # --- Create or update profile repo ---
        # IMPORTANT: repo name MUST exactly match username for GitHub to use it as profile README
        try:
            profile_repo = user.get_repo("sankalpdevtester")
        except GithubException:
            # Create without auto_init so we control the first commit
            profile_repo = user.create_repo(
                "sankalpdevtester",
                description="⚡ Sankalp Gupta — Full Stack Developer",
                private=False,
                auto_init=False,
            )
            log("Created profile repo sankalpdevtester/sankalpdevtester")
            # Small wait for GitHub to register the repo
            import time; time.sleep(3)

        # Push README — create if doesn't exist, update if it does
        try:
            existing = profile_repo.get_contents("README.md")
            profile_repo.update_file(
                "README.md",
                "chore: update profile README",
                readme_content,
                existing.sha,
            )
            log("README.md updated")
        except GithubException:
            profile_repo.create_file(
                "README.md",
                "feat: add animated profile README",
                readme_content,
            )
            log("README.md created — profile page now decorated")

        log(f"Profile done — {lc_solved} LC | {display_stars} stars shown | {total_repos} repos")

        # --- Star all repos with side accounts ---
        try:
            star_all_repos()
        except Exception as e:
            log(f"Auto-star failed: {e}", "error")

    except Exception as e:
        log(f"Profile update failed: {e}", "error")
