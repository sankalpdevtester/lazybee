import httpx
import asyncio
import random
import os
import re
from app.services.gemini_service import _ask

LEETCODE_GQL = "https://leetcode.com/graphql"
LEETCODE_USERNAME = "q9hZI5XkeT"

def _get_session():
    return os.getenv("LEETCODE_SESSION", "")

def _get_csrf():
    return os.getenv("LEETCODE_CSRF", "")

def _check_auth():
    if not _get_session(): return "LEETCODE_SESSION not set"
    if not _get_csrf(): return "LEETCODE_CSRF not set"
    return None

def _headers():
    return {
        "Content-Type": "application/json",
        "Cookie": f"LEETCODE_SESSION={_get_session()}; csrftoken={_get_csrf()}",
        "x-csrftoken": _get_csrf(),
        "Referer": "https://leetcode.com",
        "Origin": "https://leetcode.com",
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
    snippets = problem.get("codeSnippets") or []
    available_langs = [s["langSlug"] for s in snippets]
    if "mysql" in available_langs and "python3" not in available_langs:
        lang = "mysql"
    elif "bash" in available_langs and "python3" not in available_langs:
        lang = "bash"
    snippet = next((s["code"] for s in snippets if s["langSlug"] == lang), "")
    difficulty = problem.get("difficulty", "Easy")
    prompt = f"""Write a {difficulty} LeetCode solution in {lang}.
Problem: {title}
Description: {content}
Starting code: {snippet}

Make it look like a student wrote it:
- Simple variable names (i, j, n, res, temp, curr)
- 1-2 casual comments
- Must be CORRECT and pass all test cases
- Do NOT redefine TreeNode, ListNode or any provided classes
- No markdown, return raw code only"""
    code = _ask(prompt)
    code = re.sub(r'^```[\w]*\n', '', code.strip())
    code = re.sub(r'\n```$', '', code.strip())
    return code.strip()

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

async def run_daily_leetcode(num_problems: int = 8):
    from app.storage import append_log
    from datetime import datetime

    def log(msg, level="info"):
        append_log(datetime.utcnow().isoformat(), "leetcode", msg, level)

    auth_err = _check_auth()
    if auth_err:
        log(f"SKIPPED: {auth_err}", "error")
        return

    groq_key = os.getenv("GROQ_API_KEY", "")
    if not groq_key:
        log("SKIPPED: GROQ_API_KEY not set", "error")
        return

    try:
        progress = await get_badge_progress()
        daily = progress.get("daily_challenge", {})
        daily_slug = daily.get("question", {}).get("titleSlug") if daily else None

        easy = await get_problems("EASY", 50)
        medium = await get_problems("MEDIUM", 50)
        hard = await get_problems("HARD", 30)
        all_problems = easy + medium + hard

        solved = await get_already_solved()
        log(f"Solved recently: {len(solved)} | Streak: {progress.get('streak', 0)} days")

        # Build priority queue - daily challenge first, then unsolved
        queue = []
        if daily_slug:
            daily_detail = await get_problem_detail(daily_slug)
            if daily_detail and daily_detail.get("questionId"):
                queue.append(daily_detail)
                log(f"Prioritizing daily: {daily_detail.get('title')}")

        # Add unsolved problems shuffled
        unsolved = [p for p in all_problems if p["titleSlug"] not in solved and p["titleSlug"] != daily_slug]
        random.shuffle(unsolved)

        # Weight: 40% easy, 40% medium, 20% hard
        easy_pool = [p for p in unsolved if p["difficulty"] == "Easy"]
        medium_pool = [p for p in unsolved if p["difficulty"] == "Medium"]
        hard_pool = [p for p in unsolved if p["difficulty"] == "Hard"]
        pool = easy_pool + medium_pool + hard_pool
        queue += pool

        # If not enough unsolved, add already solved ones as fallback
        if len(queue) < num_problems * 3:
            fallback = [p for p in all_problems if p["titleSlug"] != daily_slug]
            random.shuffle(fallback)
            queue += fallback

        submitted = 0
        attempted = 0
        max_attempts = num_problems * 4  # try up to 4x more problems to get 5 successes

        for problem in queue:
            if submitted >= num_problems:
                break
            if attempted >= max_attempts:
                log(f"Reached max attempts ({max_attempts}), submitted {submitted}/{num_problems}")
                break

            attempted += 1
            try:
                slug = problem.get("titleSlug")
                if not slug:
                    continue

                detail = problem if problem.get("questionId") else await get_problem_detail(slug)
                if not detail or not detail.get("questionId"):
                    continue

                if submitted > 0:
                    delay = random.randint(90, 360)
                    log(f"Waiting {delay}s before next submission...")
                    await asyncio.sleep(delay)

                # Try up to 2 times per problem with different code
                success = False
                for attempt in range(2):
                    code = generate_human_like_solution(detail, "python3")
                    if not code or len(code) < 10:
                        continue
                    result = await submit_solution(slug, code, "python3")
                    submission_id = result.get("submission_id")
                    if submission_id:
                        log(f"Submitted ({submitted+1}/{num_problems}): {detail.get('title')} ({detail.get('difficulty')}) - id: {submission_id}")
                        submitted += 1
                        success = True
                        break
                    else:
                        log(f"Retry {attempt+1} for {detail.get('title')}: {result}")
                        await asyncio.sleep(10)

                if not success:
                    log(f"Skipping {detail.get('title')} after 2 failed attempts", "error")

            except Exception as e:
                log(f"Error on {problem.get('title', problem.get('titleSlug', ''))}: {e}", "error")
                continue

        log(f"LeetCode session done: {submitted}/{num_problems} submitted")

        badges = await get_badges()
        earned = badges.get("earned", [])
        upcoming = badges.get("upcoming", [])
        log(f"Badges: {len(earned)} earned | Upcoming: {[b['name'] for b in upcoming]}")

    except Exception as e:
        log(f"LeetCode run failed: {e}", "error")
