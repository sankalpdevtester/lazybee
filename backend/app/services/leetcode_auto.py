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
    """Minimal headers that match what worked before."""
    session = _get_session()
    csrf = _get_csrf()
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
      ) { questions: data { titleSlug title difficulty } }
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

def _detect_lang(detail: dict) -> str:
    snippets = detail.get("codeSnippets") or []
    available = [s["langSlug"] for s in snippets]
    if "mysql" in available and "python3" not in available:
        return "mysql"
    if "bash" in available and "python3" not in available:
        return "bash"
    return "python3"

def generate_solution(problem: dict, lang: str = "python3") -> str:
    title = problem.get("title", "")
    content = (problem.get("content", "") or "")[:800]
    snippets = problem.get("codeSnippets") or []
    snippet = next((s["code"] for s in snippets if s["langSlug"] == lang), "")
    difficulty = problem.get("difficulty", "Easy")

    prompt = f"""Solve this LeetCode {difficulty} problem in {lang}. Must pass ALL test cases with NO Time Limit Exceeded.

Problem: {title}
{content}

Starting code:
{snippet}

Rules:
- Use OPTIMAL time complexity — never O(n^2) when O(n) exists
- Tree: iterative BFS/DFS with queue/stack
- String: sliding window or hash map
- Array: two pointers or sorting
- 100% correct, all edge cases handled
- Do NOT redefine TreeNode, ListNode, or any provided classes
- Return raw code only, no markdown backticks"""

    code = _ask(prompt)
    code = re.sub(r'^```[\w]*\n', '', code.strip())
    code = re.sub(r'\n```$', '', code.strip())
    return code.strip()

async def submit_solution(slug: str, question_id: str, code: str, lang: str) -> dict:
    """Submit exactly like a browser would — no redirect following, minimal headers."""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"https://leetcode.com/problems/{slug}/submit/",
            json={"lang": lang, "question_id": question_id, "typed_code": code},
            headers=_headers(),
        )
        if r.status_code == 403:
            raise RuntimeError(f"403 — LeetCode rejected the session cookie. Update LEETCODE_SESSION on Render.")
        if r.status_code not in (200, 201):
            raise RuntimeError(f"Submit returned HTTP {r.status_code}: {r.text[:150]}")
        return r.json()

async def check_result(submission_id: int) -> str:
    """Poll for submission result until SUCCESS or timeout."""
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

    # Pre-flight checks
    auth_err = _check_auth()
    if auth_err:
        log(f"SKIPPED: {auth_err}", "error")
        return
    if not os.getenv("GROQ_API_KEY", ""):
        log("SKIPPED: GROQ_API_KEY not set", "error")
        return

    try:
        progress = await get_badge_progress()
        daily = progress.get("daily_challenge", {})
        daily_slug = daily.get("question", {}).get("titleSlug") if daily else None
        today = datetime.utcnow().strftime("%Y-%m-%d")

        # Merge persistent solved set with LC API
        state = read_json("leetcode_state")
        persistent_solved = set(state.get("solved", []))
        api_solved = await get_already_solved()
        all_solved = persistent_solved | api_solved
        log(f"Solved: {len(all_solved)} total | Streak: {progress.get('streak', 0)} days")

        # Fetch problems
        easy = await get_problems("EASY", 100)
        medium = await get_problems("MEDIUM", 100)
        hard = await get_problems("HARD", 50)
        all_problems = easy + medium + hard

        # Build queue — daily first, then unsolved easy/medium/hard
        queue = []
        last_daily = state.get("last_daily_date", "")
        if daily_slug and last_daily != today and daily_slug not in all_solved:
            d = await get_problem_detail(daily_slug)
            if d and d.get("questionId"):
                queue.append(d)
                log(f"Daily: {d.get('title')}")

        unsolved = [p for p in all_problems if p["titleSlug"] not in all_solved and p["titleSlug"] != daily_slug]
        random.shuffle(unsolved)
        queue += [p for p in unsolved if p["difficulty"] == "Easy"]
        queue += [p for p in unsolved if p["difficulty"] == "Medium"]
        queue += [p for p in unsolved if p["difficulty"] == "Hard"]

        log(f"Queue: {len(queue)} unsolved available, targeting {num_problems} accepted")

        submitted = 0
        newly_solved = set()
        consecutive_403 = 0

        for problem in queue:
            if submitted >= num_problems:
                break
            if consecutive_403 >= 3:
                log("3 consecutive 403s — session blocked, stopping. Update LEETCODE_SESSION on Render.", "error")
                break

            try:
                slug = problem.get("titleSlug")
                if not slug:
                    continue

                detail = problem if problem.get("questionId") else await get_problem_detail(slug)
                if not detail or not detail.get("questionId"):
                    continue

                if submitted > 0:
                    delay = random.randint(15, 35)
                    log(f"Waiting {delay}s...")
                    await asyncio.sleep(delay)

                lang = _detect_lang(detail)

                # Generate and submit — up to 3 attempts per problem
                success = False
                for attempt in range(3):
                    code = generate_solution(detail, lang)
                    if not code or len(code) < 10:
                        continue

                    result = await submit_solution(slug, detail["questionId"], code, lang)
                    submission_id = result.get("submission_id")
                    if not submission_id:
                        log(f"No submission_id for {detail.get('title')}: {str(result)[:100]}", "error")
                        await asyncio.sleep(8)
                        continue

                    consecutive_403 = 0
                    status = await check_result(submission_id)
                    log(f"({submitted+1}/{num_problems}) {detail.get('title')} [{detail.get('difficulty')}] [{lang}] -> {status}")

                    if status == "Accepted":
                        submitted += 1
                        success = True
                        newly_solved.add(slug)
                        if slug == daily_slug:
                            state["last_daily_date"] = today
                        await asyncio.sleep(random.randint(20, 40))
                        break
                    elif status == "Time Limit Exceeded" and attempt < 2:
                        log(f"TLE on attempt {attempt+1}, retrying with optimized solution...")
                        await asyncio.sleep(5)
                    elif attempt < 2:
                        log(f"Got {status}, retrying...")
                        await asyncio.sleep(5)

                if not success:
                    log(f"Skipping {detail.get('title')} after 3 attempts")

            except RuntimeError as e:
                if "403" in str(e):
                    consecutive_403 += 1
                    log(f"{e} (consecutive: {consecutive_403})", "error")
                    await asyncio.sleep(90)
                else:
                    log(f"Error on {problem.get('title', slug)}: {e}", "error")
            except Exception as e:
                log(f"Error on {problem.get('title', problem.get('titleSlug', ''))}: {e}", "error")

        # Persist solved slugs permanently
        if newly_solved:
            state["solved"] = list(persistent_solved | api_solved | newly_solved)
            write_json("leetcode_state", state)
            log(f"Saved {len(newly_solved)} new solved (total: {len(state['solved'])})")

        log(f"Done: {submitted}/{num_problems} accepted")
        badges = await get_badges()
        log(f"Badges: {len(badges.get('earned', []))} earned | Upcoming: {[b['name'] for b in badges.get('upcoming', [])]}")

    except Exception as e:
        log(f"LeetCode run failed: {e}", "error")
