import httpx
import time
from datetime import datetime, timedelta, timezone
from github import Github, Auth, GithubException
from collections import defaultdict

# Simple in-memory cache: { key: (data, expires_at) }
_cache: dict = {}
CACHE_TTL = 600  # 10 minutes

def _cached(key: str):
    entry = _cache.get(key)
    if entry and time.time() < entry[1]:
        return entry[0]
    return None

def _set_cache(key: str, data):
    _cache[key] = (data, time.time() + CACHE_TTL)
    return data

def _github(token: str) -> Github:
    if token:
        return Github(auth=Auth.Token(token))
    return Github()  # unauthenticated, public data only

def _get_repos(user):
    return list(user.get_repos(affiliation="owner"))

def _get_repos_public(user):
    """For display-only accounts with no token - public repos only."""
    return list(user.get_repos(type="public"))


async def get_account_stats(username: str, token: str) -> dict:
    key = f"stats:{username}"
    cached = _cached(key)
    if cached:
        return cached
    try:
        g = _github(token)
        user = g.get_user(username) if not token else g.get_user()
        repos = list(user.get_repos(type="public")) if not token else _get_repos(user)
        total_stars = sum(r.stargazers_count for r in repos)
        total_forks = sum(r.forks_count for r in repos)
        return _set_cache(key, {
            "username": username,
            "name": user.name or username,
            "bio": user.bio,
            "location": user.location,
            "company": user.company,
            "blog": user.blog,
            "public_repos": user.public_repos,
            "total_repos": len(repos),
            "followers": user.followers,
            "following": user.following,
            "total_stars": total_stars,
            "total_forks": total_forks,
            "avatar_url": user.avatar_url,
            "profile_url": user.html_url,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "display_only": not token,
        })
    except GithubException as e:
        return {"username": username, "error": str(e)}


async def get_languages(username: str, token: str) -> dict:
    key = f"langs:{username}"
    cached = _cached(key)
    if cached:
        return cached
    if not token:
        return _set_cache(key, {})
    try:
        g = _github(token)
        user = g.get_user()
        repos = _get_repos(user)
        languages = defaultdict(int)
        top_repos = sorted(repos, key=lambda r: r.stargazers_count, reverse=True)[:5]
        for repo in top_repos:
            try:
                for lang, b in repo.get_languages().items():
                    languages[lang] += b
            except Exception:
                pass
        total_bytes = sum(languages.values()) or 1
        result = {
            lang: round((b / total_bytes) * 100, 1)
            for lang, b in sorted(languages.items(), key=lambda x: -x[1])[:6]
        }
        return _set_cache(key, result)
    except Exception:
        return {}


async def get_contribution_graph(username: str, token: str) -> dict:
    key = f"graph:{username}"
    cached = _cached(key)
    if cached:
        return cached
    # For display-only accounts with no token, use public contribution endpoint
    auth_header = f"Bearer {token}" if token else "Bearer "
    query = """
    query($username: String!) {
      user(login: $username) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays { date contributionCount }
            }
          }
        }
      }
    }
    """
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                "https://api.github.com/graphql",
                json={"query": query, "variables": {"username": username}},
                headers={"Authorization": auth_header},
            )
            data = r.json()
            calendar = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
            grid = {}
            for week in calendar["weeks"]:
                for day in week["contributionDays"]:
                    grid[day["date"]] = day["contributionCount"]
            current_streak, longest_streak = _calc_streaks(grid)
            return _set_cache(key, {
                "username": username,
                "grid": grid,
                "total_contributions": calendar["totalContributions"],
                "current_streak": current_streak,
                "longest_streak": longest_streak,
            })
    except Exception as e:
        return {"username": username, "error": str(e), "grid": {}}


def _calc_streaks(grid: dict) -> tuple[int, int]:
    days = sorted(grid.keys(), reverse=True)
    current = 0
    for day in days:
        if grid[day] > 0:
            current += 1
        else:
            break
    longest = running = 0
    for day in sorted(grid.keys()):
        if grid[day] > 0:
            running += 1
            longest = max(longest, running)
        else:
            running = 0
    return current, longest


async def get_all_repos(username: str, token: str) -> list:
    key = f"repos:{username}"
    cached = _cached(key)
    if cached:
        return cached
    try:
        g = _github(token)
        user = g.get_user(username) if not token else g.get_user()
        repos = list(user.get_repos(type="public")) if not token else _get_repos(user)
        repos.sort(key=lambda r: r.updated_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        result = []
        for r in repos:
            try:
                result.append({
                    "name": r.name,
                    "description": r.description,
                    "url": r.html_url,
                    "stars": r.stargazers_count,
                    "forks": r.forks_count,
                    "language": r.language,
                    "private": r.private,
                    "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                })
            except Exception:
                pass
        return _set_cache(key, result)
    except GithubException as e:
        return [{"error": str(e)}]


def create_repo_and_init(token: str, repo_name: str, description: str, readme_content: str) -> str:
    g = _github(token)
    user = g.get_user()
    repo = user.create_repo(name=repo_name, description=description, private=False, auto_init=False)
    repo.create_file("README.md", "initial commit: project scaffold", readme_content)
    return repo.html_url


def commit_file(token: str, repo_name: str, file_path: str, content: str, message: str):
    g = _github(token)
    user = g.get_user()
    repo = user.get_repo(repo_name)
    try:
        existing = repo.get_contents(file_path)
        repo.update_file(file_path, message, content, existing.sha)
    except GithubException:
        repo.create_file(file_path, message, content)
