import httpx
import asyncio
import random
import os
from app.services.gemini_service import _ask

LEETCODE_GQL = "https://leetcode.com/graphql"
LEETCODE_SESSION = os.getenv("LEETCODE_SESSION", "")
CSRF_TOKEN = os.getenv("LEETCODE_CSRF", "")
LEETCODE_USERNAME = "q9hZI5XkeT"

def _headers():
    return {
        "Content-Type": "application/json",
        "Cookie": f"LEETCODE_SESSION={LEETCODE_SESSION}; csrftoken={CSRF_TOKEN}",
        "x-csrftoken": CSRF_TOKEN,
        "Referer": "https://leetcode.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

async def _gql(query: str, variables: dict = {}) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(LEETCODE_GQL, json={"query": query, "variables": variables}, headers=_headers())
        return r.json()

async def get_problems(difficulty: str = "EASY", limit: int = 50) -> list:
    query = """
    query($limit: Int, $filters: QuestionListFilterInput) {
      problemsetQuestionList: questionList(
        categorySlug: "" limit: $limit skip: 0 filters: $filters
      ) {
        questions: data { titleSlug title difficulty }
      }
    }
    """
    data = await _gql(query, {"limit": limit, "filters": {"difficulty": difficulty}})
    return data.get("data", {}).get("problemsetQuestionList", {}).get("questions", [])

async def get_already_solved() -> set:
    query = """
    query($username: String!) {
      recentAcSubmissionList(username: $username, limit: 100) { titleSlug }
    }
    """
    data = await _gql(query, {"username": LEETCODE_USERNAME})
    subs = data.get("data", {}).get("recentAcSubmissionList", []) or []
    return {s["titleSlug"] for s in subs}

async def get_problem_detail(slug: str) -> dict:
    query = """
    query($titleSlug: String!) {
      question(titleSlug: $titleSlug) {
        questionId title titleSlug content difficulty
        codeSnippets { lang langSlug code }
      }
    }
    """
    data = await _gql(query, {"titleSlug": slug})
    return data.get("data", {}).get("question", {})

async def get_badges() -> dict:
    query = """
    query($username: String!) {
      matchedUser(username: $username) {
        badges { id name icon displayName }
        upcomingBadges { name icon }
      }
    }
    """
    data = await _gql(query, {"username": LEETCODE_USERNAME})
    user = data.get("data", {}).get("matchedUser", {})
    return {
        "earned": user.get("badges", []),
        "upcoming": user.get("upcomingBadges", []),
    }

async def get_badge_progress() -> dict:
    """Check what problems to solve to earn upcoming badges."""
    query = """
    query($username: String!) {
      matchedUser(username: $username) {
        submitStats {
          acSubmissionNum { difficulty count }
        }
        userCalendar { streak totalActiveDays }
      }
      activeDailyCodingChallengeQuestion {
        date
        question { titleSlug title difficulty }
      }
    }
    """
    data = await _gql(query, {"username": LEETCODE_USERNAME})
    user = data.get("data", {}).get("matchedUser", {})
    daily = data.get("data", {}).get("activeDailyCodingChallengeQuestion", {})
    stats = {s["difficulty"]: s["count"] for s in user.get("submitStats", {}).get("acSubmissionNum", [])}
    calendar = user.get("userCalendar", {})
    return {
        "solved": stats,
        "streak": calendar.get("streak", 0),
        "active_days": calendar.get("totalActiveDays", 0),
        "daily_challenge": daily,
    }

def generate_human_like_solution(problem: dict, lang: str = "python3") -> str:
    title = problem.get("title", "")
    content = (problem.get("content", "") or "")[:600]
    snippet = next((s["code"] for s in (problem.get("codeSnippets") or []) if s["langSlug"] == lang), "")
    difficulty = problem.get("difficulty", "Easy")
    prompt = f"""Write a {difficulty} LeetCode solution in {lang}.
Problem: {title}
Description: {content}
Starting code: {snippet}

Make it look like a student wrote it:
- Simple variable names (i, j, n, res, temp, curr)
- 1-2 casual comments like # handle edge case or # check boundary  
- Slightly verbose, not clever one-liners
- One small redundant check is fine
- For Hard problems: use correct algorithm but with slightly suboptimal variable naming
- Must be CORRECT and pass all test cases
- No markdown, return raw code only"""
    return _ask(prompt)

async def submit_solution(slug: str, code: str, lang: str = "python3") -> dict:
    detail = await get_problem_detail(slug)
    question_id = detail.get("questionId")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"https://leetcode.com/problems/{slug}/submit/",
            json={"lang": lang, "question_id": question_id, "typed_code": code},
            headers=_headers(),
        )
        return r.json()

async def run_daily_leetcode(num_problems: int = 5):
    from app.storage import append_log
    from datetime import datetime

    def log(msg, level="info"):
        append_log(datetime.utcnow().isoformat(), "leetcode", msg, level)

    try:
        # Always solve the daily challenge first (helps with badges)
        progress = await get_badge_progress()
        daily = progress.get("daily_challenge", {})
        daily_slug = daily.get("question", {}).get("titleSlug") if daily else None

        # Get mix of easy, medium, hard
        easy = await get_problems("EASY", 30)
        medium = await get_problems("MEDIUM", 30)
        hard = await get_problems("HARD", 20)
        all_problems = easy + medium + hard

        solved = await get_already_solved()
        log(f"Solved recently: {len(solved)} | Streak: {progress.get('streak', 0)} days")

        unsolved = [p for p in all_problems if p["titleSlug"] not in solved]
        if not unsolved:
            unsolved = all_problems

        # Prioritize daily challenge for badge progress
        to_solve = []
        if daily_slug and daily_slug not in solved:
            daily_detail = await get_problem_detail(daily_slug)
            if daily_detail:
                to_solve.append(daily_detail)
                log(f"Prioritizing daily challenge: {daily.get('question', {}).get('title')}")

        # Fill remaining slots with mix of difficulties
        remaining = [p for p in unsolved if p["titleSlug"] != daily_slug]
        # Weight: 40% easy, 40% medium, 20% hard
        easy_pool = [p for p in remaining if p["difficulty"] == "Easy"]
        medium_pool = [p for p in remaining if p["difficulty"] == "Medium"]
        hard_pool = [p for p in remaining if p["difficulty"] == "Hard"]

        slots = num_problems - len(to_solve)
        picks = (
            random.sample(easy_pool, min(int(slots * 0.4) + 1, len(easy_pool))) +
            random.sample(medium_pool, min(int(slots * 0.4) + 1, len(medium_pool))) +
            random.sample(hard_pool, min(int(slots * 0.2) + 1, len(hard_pool)))
        )
        to_solve += picks[:slots]

        for i, problem in enumerate(to_solve[:num_problems]):
            try:
                slug = problem.get("titleSlug") or problem.get("titleSlug")
                if not slug:
                    continue

                detail = problem if problem.get("questionId") else await get_problem_detail(slug)
                if not detail or not detail.get("questionId"):
                    continue

                code = generate_human_like_solution(detail, "python3")
                if not code or len(code) < 10:
                    log(f"Empty code for {slug}", "error")
                    continue

                if i > 0:
                    delay = random.randint(90, 360)
                    log(f"Waiting {delay}s...")
                    await asyncio.sleep(delay)

                result = await submit_solution(slug, code, "python3")
                submission_id = result.get("submission_id", "unknown")
                log(f"Submitted: {detail.get('title')} ({detail.get('difficulty')}) - id: {submission_id}")

            except Exception as e:
                log(f"Failed {problem.get('title', '')}: {e}", "error")
                continue

        # Log badge status after solving
        badges = await get_badges()
        earned = badges.get("earned", [])
        upcoming = badges.get("upcoming", [])
        log(f"Badges earned: {len(earned)} | Upcoming: {[b['name'] for b in upcoming]}")

    except Exception as e:
        log(f"LeetCode run failed: {e}", "error")
