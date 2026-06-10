import httpx
import asyncio
import random
import re
import os
from app.services.gemini_service import _ask

LEETCODE_GQL = "https://leetcode.com/graphql"
LEETCODE_USERNAME = "q9hZI5XkeT"

def _headers():
    session = os.getenv("LEETCODE_SESSION", "").strip()
    csrf = os.getenv("LEETCODE_CSRF", "").strip()
    return {
        "Content-Type": "application/json",
        "Cookie": f"LEETCODE_SESSION={session}; csrftoken={csrf}",
        "x-csrftoken": csrf,
        "Referer": "https://leetcode.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

async def _gql(query: str, variables: dict = {}) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(LEETCODE_GQL, json={"query": query, "variables": variables}, headers=_headers())
        return r.json()

async def get_problems(difficulty: str = "EASY", limit: int = 100) -> list:
    query = """
    query($limit: Int, $filters: QuestionListFilterInput) {
      problemsetQuestionList: questionList(
        categorySlug: "" limit: $limit skip: 0 filters: $filters
      ) { questions: data { titleSlug title difficulty isPaidOnly } }
    }
    """
    data = await _gql(query, {"limit": limit, "filters": {"difficulty": difficulty}})
    problems = data.get("data", {}).get("problemsetQuestionList", {}).get("questions", [])
    # Filter out premium/paid problems immediately
    return [p for p in problems if not p.get("isPaidOnly", False)]

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
        questionId title titleSlug content difficulty isPaidOnly
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
    return {"earned": user.get("badges", []), "upcoming": user.get("upcomingBadges", [])}

async def get_badge_progress() -> dict:
    query = """
    query($username: String!) {
      matchedUser(username: $username) {
        submitStats { acSubmissionNum { difficulty count } }
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
    prompt = f"""Solve this LeetCode {difficulty} problem in {lang}. Must pass ALL test cases with NO Time Limit Exceeded.
Problem: {title}
{content}
Starting code: {snippet}

Rules:
- Use OPTIMAL time complexity — never O(n^2) when O(n) exists
- Must be 100% correct and handle all edge cases
- Do NOT redefine TreeNode, ListNode, or any provided classes
- No markdown backticks, return raw code only"""
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
        if not r.text.strip():
            raise RuntimeError(f"Empty response from LeetCode for {slug} — likely premium/locked problem")
        return r.json()

async def check_result(submission_id: int) -> str:
    async with httpx.AsyncClient(timeout=60) as client:
        for _ in range(20):
            await asyncio.sleep(3)
            try:
                r = await client.get(
                    f"https://leetcode.com/submissions/detail/{submission_id}/check/",
                    headers=_headers(),
                )
                if r.status_code != 200:
                    continue
                data = r.json()
                state = data.get("state", "")
                if state == "SUCCESS":
                    return data.get("status_msg", "Unknown")
                if state in ("PENDING", "STARTED"):
                    continue
                return state or "Unknown"
            except Exception:
                continue
    return "Timeout"

async def run_daily_leetcode(num_problems: int = 26):
    from app.storage import append_log, read_json, write_json
    from datetime import datetime

    def log(msg, level="info"):
        append_log(datetime.utcnow().isoformat(), "leetcode", msg, level)

    session = os.getenv("LEETCODE_SESSION", "").strip()
    csrf = os.getenv("LEETCODE_CSRF", "").strip()
    if not session or not csrf:
        log("SKIPPED: LEETCODE_SESSION or LEETCODE_CSRF not set", "error")
        return
    if not os.getenv("GROQ_API_KEY", ""):
        log("SKIPPED: GROQ_API_KEY not set", "error")
        return

    log(f"Session: {len(session)} chars, IP check: {session[session.find('ip')+5:session.find('ip')+20] if 'ip' in session else 'n/a'}")

    try:
        progress = await get_badge_progress()
        daily = progress.get("daily_challenge", {})
        daily_slug = daily.get("question", {}).get("titleSlug") if daily else None
        today = datetime.utcnow().strftime("%Y-%m-%d")

        state = read_json("leetcode_state")
        persistent_solved = set(state.get("solved", []))
        api_solved = await get_already_solved()
        all_solved = persistent_solved | api_solved
        log(f"Solved: {len(all_solved)} total | Streak: {progress.get('streak', 0)} days")

        # Fetch free problems only (isPaidOnly filtered in get_problems)
        easy = await get_problems("EASY", 100)
        medium = await get_problems("MEDIUM", 100)
        hard = await get_problems("HARD", 50)
        all_problems = easy + medium + hard

        queue = []
        last_daily = state.get("last_daily_date", "")
        if daily_slug and last_daily != today and daily_slug not in all_solved:
            daily_detail = await get_problem_detail(daily_slug)
            if daily_detail and daily_detail.get("questionId") and not daily_detail.get("isPaidOnly"):
                queue.append(daily_detail)
                log(f"Daily: {daily_detail.get('title')}")

        unsolved = [p for p in all_problems if p["titleSlug"] not in all_solved and p["titleSlug"] != daily_slug]
        random.shuffle(unsolved)
        queue += [p for p in unsolved if p["difficulty"] == "Easy"]
        queue += [p for p in unsolved if p["difficulty"] == "Medium"]
        queue += [p for p in unsolved if p["difficulty"] == "Hard"]

        log(f"Queue: {len(queue)} free unsolved, targeting {num_problems} accepted")

        submitted = 0
        attempted = 0
        max_attempts = num_problems * 4
        newly_solved = set()

        for problem in queue:
            if submitted >= num_problems:
                break
            if attempted >= max_attempts:
                log(f"Reached max attempts, got {submitted}/{num_problems}")
                break

            attempted += 1
            try:
                slug = problem.get("titleSlug")
                if not slug:
                    continue

                detail = problem if problem.get("questionId") else await get_problem_detail(slug)
                if not detail or not detail.get("questionId"):
                    continue

                # Skip premium problems
                if detail.get("isPaidOnly") or not detail.get("codeSnippets"):
                    log(f"Skipping premium: {detail.get('title', slug)}")
                    continue

                if submitted > 0:
                    delay = random.randint(30, 90)
                    log(f"Waiting {delay}s...")
                    await asyncio.sleep(delay)

                snippets = detail.get("codeSnippets") or []
                available = [s["langSlug"] for s in snippets]
                if "mysql" in available and "python3" not in available:
                    lang = "mysql"
                elif "bash" in available and "python3" not in available:
                    lang = "bash"
                else:
                    lang = "python3"

                success = False
                for attempt in range(3):
                    code = generate_human_like_solution(detail, lang)
                    if not code or len(code) < 10:
                        continue
                    result = await submit_solution(slug, code, lang)
                    submission_id = result.get("submission_id")
                    if not submission_id:
                        log(f"Retry {attempt+1} for {detail.get('title')}: {str(result)[:80]}")
                        await asyncio.sleep(10)
                        continue

                    status = await check_result(submission_id)
                    log(f"({submitted+1}/{num_problems}) {detail.get('title')} ({detail.get('difficulty')}) [{lang}] -> {status}")

                    if status == "Accepted":
                        submitted += 1
                        success = True
                        newly_solved.add(slug)
                        if slug == daily_slug:
                            state["last_daily_date"] = today
                        break
                    elif attempt < 2:
                        log(f"Got {status}, retrying...")
                        await asyncio.sleep(5)

                if not success:
                    log(f"Skipping {detail.get('title')} after 3 attempts")

            except Exception as e:
                log(f"Error on {problem.get('title', problem.get('titleSlug', ''))}: {e}", "error")
                continue

        if newly_solved:
            state["solved"] = list(persistent_solved | api_solved | newly_solved)
            write_json("leetcode_state", state)
            log(f"Saved {len(newly_solved)} new solved (total: {len(state['solved'])})")

        log(f"Session done: {submitted}/{num_problems} accepted")
        badges = await get_badges()
        log(f"Badges: {len(badges.get('earned', []))} earned | Upcoming: {[b['name'] for b in badges.get('upcoming', [])]}")

    except Exception as e:
        log(f"LeetCode run failed: {e}", "error")
