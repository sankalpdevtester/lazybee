import httpx
import asyncio
import random
import re
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
- 1-2 casual comments like # handle edge case
- Must be CORRECT and pass all test cases
- No markdown, no backticks, return raw code only"""
    code = _ask(prompt)
    # Strip markdown backticks if model added them
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

async def check_submission_result(submission_id: int) -> str:
    """Poll until we get the actual result."""
    async with httpx.AsyncClient(timeout=60) as client:
        for _ in range(20):
            await asyncio.sleep(3)
            r = await client.get(
                f"https://leetcode.com/submissions/detail/{submission_id}/check/",
                headers=_headers(),
            )
            data = r.json()
            state = data.get("state", "")
            if state == "SUCCESS":
                return data.get("status_msg", "Unknown")
            elif state in ("PENDING", "STARTED"):
                continue
            else:
                return state or "Unknown"
    return "Timeout"

async def run_daily_leetcode(num_problems: int = 5):
    from app.storage import append_log, read_json, write_json
    from datetime import datetime

    def log(msg, level="info"):
        append_log(datetime.utcnow().isoformat(), "leetcode", msg, level)

    try:
        progress = await get_badge_progress()
        daily = progress.get("daily_challenge", {})
        daily_slug = daily.get("question", {}).get("titleSlug") if daily else None
        today = datetime.utcnow().strftime("%Y-%m-%d")

        # Load persistent state from Redis
        lc_state = read_json("leetcode_state")
        our_solved = set(lc_state.get("solved", []))
        last_daily_date = lc_state.get("last_daily_date", "")

        # Merge with LeetCode's own AC list
        lc_ac = await get_already_solved()
        all_solved = our_solved | lc_ac

        log(f"Total solved tracked: {len(all_solved)} | Streak: {progress.get('streak', 0)} days")

        easy = await get_problems("EASY", 100)
        medium = await get_problems("MEDIUM", 100)
        hard = await get_problems("HARD", 50)
        all_problems = easy + medium + hard

        # Build queue
        queue = []

        # Daily challenge - only if not done today
        if daily_slug and last_daily_date != today and daily_slug not in all_solved:
            daily_detail = await get_problem_detail(daily_slug)
            if daily_detail and daily_detail.get("questionId"):
                queue.append(daily_detail)
                log(f"Daily: {daily_detail.get('title')}")
        elif daily_slug and (last_daily_date == today or daily_slug in all_solved):
            log(f"Daily already done today, skipping")

        # Build unsolved pools
        unsolved = [p for p in all_problems if p["titleSlug"] not in all_solved and p["titleSlug"] != daily_slug]
        easy_pool = [p for p in unsolved if p["difficulty"] == "Easy"]
        medium_pool = [p for p in unsolved if p["difficulty"] == "Medium"]
        hard_pool = [p for p in unsolved if p["difficulty"] == "Hard"]

        log(f"Unsolved: {len(easy_pool)} easy, {len(medium_pool)} medium, {len(hard_pool)} hard")

        slots = num_problems - len(queue)
        n_hard = max(1, slots // 5)
        n_medium = max(1, slots // 3)
        n_easy = max(1, slots - n_hard - n_medium)

        if hard_pool:
            queue += random.sample(hard_pool, min(n_hard, len(hard_pool)))
        if medium_pool:
            queue += random.sample(medium_pool, min(n_medium, len(medium_pool)))
        if easy_pool:
            queue += random.sample(easy_pool, min(n_easy, len(easy_pool)))

        # Only pad if we don't have enough - use unsolved only
        if len(queue) < num_problems:
            extra = [p for p in unsolved if p["titleSlug"] not in {q.get("titleSlug") for q in queue}]
            random.shuffle(extra)
            queue += extra[:num_problems - len(queue)]

        log(f"Queue: {len(queue)} problems to solve")

        submitted = 0
        session_tried = set()

        for problem in queue:
            if submitted >= num_problems:
                break

            slug = problem.get("titleSlug")
            if not slug or slug in session_tried:
                continue
            session_tried.add(slug)

            try:
                detail = problem if problem.get("questionId") else await get_problem_detail(slug)
                if not detail or not detail.get("questionId"):
                    continue

                if submitted > 0:
                    delay = random.randint(60, 240)
                    log(f"Waiting {delay}s...")
                    await asyncio.sleep(delay)

                success = False
                for attempt in range(3):
                    code = generate_human_like_solution(detail, "python3")
                    if not code or len(code) < 10:
                        continue
                    result = await submit_solution(slug, code, "python3")
                    submission_id = result.get("submission_id")
                    if not submission_id:
                        log(f"No submission_id for {detail.get('title')}: {str(result)[:100]}", "error")
                        break
                    status = await check_submission_result(submission_id)
                    log(f"({submitted+1}/{num_problems}) {detail.get('title')} ({detail.get('difficulty')}) → {status}")
                    if status == "Accepted":
                        submitted += 1
                        success = True
                        our_solved.add(slug)
                        if slug == daily_slug:
                            lc_state["last_daily_date"] = today
                        break
                    else:
                        if attempt < 2:
                            log(f"Got {status}, retrying...")
                            await asyncio.sleep(5)

                if not success:
                    log(f"Could not solve {detail.get('title')} - skipping")

            except Exception as e:
                log(f"Error on {problem.get('title', slug)}: {e}", "error")
                continue

        lc_state["solved"] = list(our_solved)
        write_json("leetcode_state", lc_state)

        log(f"✅ Session done: {submitted}/{num_problems} accepted")
        badges = await get_badges()
        log(f"Badges: {len(badges.get('earned', []))} earned | Upcoming: {[b['name'] for b in badges.get('upcoming', [])]}")

    except Exception as e:
        log(f"LeetCode run failed: {e}", "error")
