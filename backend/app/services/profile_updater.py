"""
Generates and pushes the animated GitHub profile README for sankalpdevtester.
Called daily by the scheduler.
"""
import os
from github import Github, Auth, GithubException
from datetime import datetime

def generate_profile_readme(stats: dict) -> str:
    total_stars = stats.get("stars", 0)
    total_repos = stats.get("repos", 0)
    lc_solved = stats.get("lc_solved", 0)
    lc_streak = stats.get("lc_streak", 0)
    top_langs = stats.get("languages", ["Python", "TypeScript", "Go"])
    contrib = stats.get("contributions", 0)

    lang_badges = " ".join([
        f"![{l}](https://img.shields.io/badge/{l.replace(' ', '%20').replace('+', '%2B').replace('#', '%23')}-informational?style=flat&logo={l.lower().replace(' ', '').replace('+', 'plus').replace('#', 'sharp')}&logoColor=white&color=6366f1)"
        for l in top_langs[:6]
    ])

    return f"""<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=180&section=header&text=Sankalp%20Gupta&fontSize=42&fontColor=fff&animation=twinkling&fontAlignY=32&desc=Full%20Stack%20Developer%20%7C%20Open%20Source%20Enthusiast&descAlignY=55&descSize=18" width="100%"/>

</div>

<div align="center">

[![Typing SVG](https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=600&size=22&duration=3000&pause=1000&color=6366F1&center=true&vCenter=true&multiline=true&width=700&height=100&lines=Building+real+things+that+work.;{total_repos}+projects+%7C+{lc_solved}+LeetCode+problems+solved;Currently+learning+something+new+every+day.)](https://git.io/typing-svg)

</div>

---

## 🧑‍💻 About Me

```yaml
name: Sankalp Gupta
role: Full Stack Developer
location: India
focus:
  - Building production-ready web applications
  - Solving complex algorithmic problems
  - Open source development
  - System design & architecture
currently_learning: Advanced DSA, Cloud Architecture
fun_fact: I let AI help commit code while I sleep 🤖
```

---

## 🚀 Stats

<div align="center">

<img height="180em" src="https://github-readme-stats.vercel.app/api?username=sankalpdevtester&show_icons=true&theme=tokyonight&include_all_commits=true&count_private=true&hide_border=true&bg_color=0d1117&title_color=6366f1&icon_color=6366f1&text_color=ffffff"/>
<img height="180em" src="https://github-readme-stats.vercel.app/api/top-langs/?username=sankalpdevtester&layout=compact&langs_count=8&theme=tokyonight&hide_border=true&bg_color=0d1117&title_color=6366f1&text_color=ffffff"/>

</div>

<div align="center">

<img src="https://github-readme-streak-stats.herokuapp.com/?user=sankalpdevtester&theme=tokyonight&hide_border=true&background=0d1117&ring=6366f1&fire=6366f1&currStreakLabel=6366f1" alt="streak"/>

</div>

<div align="center">

![Activity Graph](https://github-readme-activity-graph.vercel.app/graph?username=sankalpdevtester&bg_color=0d1117&color=6366f1&line=6366f1&point=ffffff&area=true&hide_border=true)

</div>

---

## 🧩 LeetCode Progress

<div align="center">

![LeetCode Stats](https://leetcard.jacoblin.cool/q9hZI5XkeT?theme=dark&font=JetBrains%20Mono&ext=heatmap&border=0&radius=20)

</div>

<div align="center">

| 🎯 Problems Solved | 🔥 Day Streak | ⭐ GitHub Stars | 📦 Public Repos |
|:-:|:-:|:-:|:-:|
| **{lc_solved}** | **{lc_streak} days** | **{total_stars}** | **{total_repos}** |

</div>

---

## 🛠️ Tech Stack

<div align="center">

### Languages
![Python](https://img.shields.io/badge/Python-informational?style=for-the-badge&logo=python&logoColor=white&color=6366f1)
![TypeScript](https://img.shields.io/badge/TypeScript-informational?style=for-the-badge&logo=typescript&logoColor=white&color=6366f1)
![JavaScript](https://img.shields.io/badge/JavaScript-informational?style=for-the-badge&logo=javascript&logoColor=white&color=6366f1)
![Go](https://img.shields.io/badge/Go-informational?style=for-the-badge&logo=go&logoColor=white&color=6366f1)
![Java](https://img.shields.io/badge/Java-informational?style=for-the-badge&logo=openjdk&logoColor=white&color=6366f1)
![Rust](https://img.shields.io/badge/Rust-informational?style=for-the-badge&logo=rust&logoColor=white&color=6366f1)

### Frameworks & Tools
![React](https://img.shields.io/badge/React-informational?style=for-the-badge&logo=react&logoColor=white&color=0ea5e9)
![FastAPI](https://img.shields.io/badge/FastAPI-informational?style=for-the-badge&logo=fastapi&logoColor=white&color=0ea5e9)
![Node.js](https://img.shields.io/badge/Node.js-informational?style=for-the-badge&logo=nodedotjs&logoColor=white&color=0ea5e9)
![Next.js](https://img.shields.io/badge/Next.js-informational?style=for-the-badge&logo=nextdotjs&logoColor=white&color=0ea5e9)
![Docker](https://img.shields.io/badge/Docker-informational?style=for-the-badge&logo=docker&logoColor=white&color=0ea5e9)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-informational?style=for-the-badge&logo=postgresql&logoColor=white&color=0ea5e9)

</div>

---

## 📌 Featured Projects

<div align="center">

[![AetherDB](https://github-readme-stats.vercel.app/api/pin/?username=sankalpdevtester&repo=aether-db&theme=tokyonight&hide_border=true&bg_color=0d1117&title_color=6366f1&icon_color=6366f1&text_color=ffffff)](https://github.com/sankalpdevtester/aether-db)
[![Synapse Editor](https://github-readme-stats.vercel.app/api/pin/?username=sankalpdevtester&repo=synapse-collaborative-editor&theme=tokyonight&hide_border=true&bg_color=0d1117&title_color=6366f1&icon_color=6366f1&text_color=ffffff)](https://github.com/sankalpdevtester/synapse-collaborative-editor)

</div>

---

## 🌐 Connect

<div align="center">

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Sankalp%20Gupta-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/sankalp-gupta)
[![LeetCode](https://img.shields.io/badge/LeetCode-q9hZI5XkeT-FFA116?style=for-the-badge&logo=leetcode&logoColor=white)](https://leetcode.com/u/q9hZI5XkeT/)
[![GitHub](https://img.shields.io/badge/GitHub-sankalpdevtester-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/sankalpdevtester)

</div>

---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=100&section=footer" width="100%"/>

<sub>⚡ Profile auto-updated daily | Last updated: {datetime.utcnow().strftime("%B %d, %Y")}</sub>

</div>
"""

def update_profile_readme():
    from app.storage import append_log, read_json
    from app.services.auto_star import star_all_repos
    from datetime import datetime

    def log(msg, level="info"):
        append_log(datetime.utcnow().isoformat(), "profile", msg, level)

    token = os.getenv("SANKALPDEVTESTER_TOKEN", "")
    if not token:
        log("No token for sankalpdevtester", "error")
        return

    try:
        g = Github(auth=Auth.Token(token))
        user = g.get_user()

        # Gather stats
        repos = list(user.get_repos(affiliation="owner"))
        total_stars = sum(r.stargazers_count for r in repos)
        total_repos = len([r for r in repos if not r.private])

        # LeetCode stats from storage
        lc_state = read_json("leetcode_state")
        lc_solved = len(lc_state.get("solved", []))

        # Top languages
        from collections import Counter
        lang_counter = Counter()
        for r in repos:
            if r.language:
                lang_counter[r.language] += 1
        top_langs = [l for l, _ in lang_counter.most_common(6)]

        stats = {
            "stars": total_stars,
            "repos": total_repos,
            "lc_solved": lc_solved,
            "lc_streak": 0,
            "languages": top_langs or ["Python", "TypeScript", "Go"],
            "contributions": 0,
        }

        readme_content = generate_profile_readme(stats)

        # Create or update the profile repo (sankalpdevtester/sankalpdevtester)
        try:
            profile_repo = user.get_repo("sankalpdevtester")
        except GithubException:
            profile_repo = user.create_repo(
                "sankalpdevtester",
                description="⚡ My GitHub profile README",
                private=False,
                auto_init=True,
            )
            log("Created profile repo sankalpdevtester/sankalpdevtester")

        try:
            existing = profile_repo.get_contents("README.md")
            profile_repo.update_file("README.md", "chore: update profile README", readme_content, existing.sha)
        except GithubException:
            profile_repo.create_file("README.md", "feat: add animated profile README", readme_content)

        log(f"Profile README updated — {lc_solved} LC solved, {total_stars} stars, {total_repos} repos")

        # Also star all repos with other accounts
        try:
            star_all_repos()
        except Exception as e:
            log(f"Auto-star failed: {e}", "error")

    except Exception as e:
        log(f"Profile update failed: {e}", "error")
