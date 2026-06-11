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
    content = (problem.get("content", "") or "")[:800]
    snippet = next((s["code"] for s in (problem.get("codeSnippets") or []) if s["langSlug"] == lang), "")
    difficulty = problem.get("difficulty", "Easy")
    prompt = f"""You are an expert competitive programmer. Solve this LeetCode {difficulty} problem CORRECTLY in {lang}.

Problem: {title}
{content}

Starting code template:
{snippet}

CRITICAL requirements:
1. The solution MUST be 100% correct and pass ALL test cases including edge cases
2. Use the most efficient algorithm - optimal time and space complexity
3. For graph/tree problems: use BFS/DFS iteratively
4. For DP problems: identify the correct recurrence relation
5. Handle ALL edge cases: empty input, single element, maximum constraints
6. Do NOT redefine TreeNode, ListNode, or any class in the template
7. Return ONLY the raw code - no markdown, no backticks, no explanation

Think through the algorithm carefully before writing code. The answer must be mathematically correct."""
    code = _ask(prompt)
    code = re.sub(r'^```[\w]*\n', '', code.strip())
    code = re.sub(r'\n```$', '', code.strip())
    return code.strip()

async def submit_solution(slug: str, question_id: str, code: str, lang: str = "python3") -> dict:
    url = f"https://leetcode.com/problems/{slug}/submit/"
    proxy_url = os.getenv("LEETCODE_PROXY_URL", "").strip()
    proxy_secret = os.getenv("LEETCODE_PROXY_SECRET", "").strip()

    async with httpx.AsyncClient(timeout=30) as client:
        if proxy_url and proxy_secret:
            # Route through Cloudflare Worker proxy to avoid AWS IP block
            r = await client.post(
                proxy_url,
                json={"url": url, "method": "POST", "headers": _headers(),
                      "data": {"lang": lang, "question_id": question_id, "typed_code": code}},
                headers={"X-Proxy-Secret": proxy_secret, "Content-Type": "application/json"},
            )
        else:
            r = await client.post(url,
                json={"lang": lang, "question_id": question_id, "typed_code": code},
                headers=_headers())

        if r.status_code in (301, 302):
            raise RuntimeError(f"Redirect {r.status_code} — session rejected")
        if r.status_code == 403:
            raise RuntimeError(f"403 — session rejected")
        if not r.text.strip():
            raise RuntimeError(f"Empty response (status {r.status_code}) — session likely rejected")
        try:
            return r.json()
        except Exception:
            raise RuntimeError(f"Non-JSON response (status {r.status_code}): {r.text[:100]}")

async def _proxy_get(url: str) -> dict:
    """GET request through Cloudflare proxy if configured, else direct."""
    proxy_url = os.getenv("LEETCODE_PROXY_URL", "").strip()
    proxy_secret = os.getenv("LEETCODE_PROXY_SECRET", "").strip()
    async with httpx.AsyncClient(timeout=30) as client:
        if proxy_url and proxy_secret:
            r = await client.post(proxy_url,
                json={"url": url, "method": "GET", "headers": _headers()},
                headers={"X-Proxy-Secret": proxy_secret, "Content-Type": "application/json"})
        else:
            r = await client.get(url, headers=_headers())
        if r.status_code != 200:
            return {}
        try: return r.json()
        except: return {}

async def check_result(submission_id: int) -> str:
    for _ in range(20):
        await asyncio.sleep(3)
        try:
            data = await _proxy_get(f"https://leetcode.com/submissions/detail/{submission_id}/check/")
            state = data.get("state", "")
            if state == "SUCCESS": return data.get("status_msg", "Unknown")
            if state in ("PENDING", "STARTED"): continue
            if state: return state
        except: continue
    return "Timeout"

async def run_daily_leetcode(num_problems: int = 5):
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
    proxy_url = os.getenv("LEETCODE_PROXY_URL", "").strip()
    log(f"Proxy: {'ACTIVE -> ' + proxy_url[:40] if proxy_url else 'DISABLED (direct to LC)'}")

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
        # Hard problems last - deprioritized due to TLE risk
        queue += [p for p in unsolved if p["difficulty"] == "Hard"]

        log(f"Queue: {len(queue)} free unsolved, targeting {num_problems} accepted")

        submitted = 0
        attempted = 0
        max_attempts = num_problems * 4
        newly_solved = set()
        consecutive_errors = 0

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
                    delay = random.randint(90, 150)
                    log(f"Waiting {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    # First submission - small warmup delay
                    await asyncio.sleep(random.randint(5, 15))

                snippets = detail.get("codeSnippets") or []
                available = [s["langSlug"] for s in snippets]
                if "mysql" in available and "python3" not in available:
                    lang = "mysql"
                elif "bash" in available and "python3" not in available:
                    lang = "bash"
                else:
                    lang = "python3"

                success = False
                code = generate_human_like_solution(detail, lang)
                if not code or len(code) < 10:
                    log(f"Empty code for {detail.get('title')}, skipping")
                    continue
                result = await submit_solution(slug, detail["questionId"], code, lang)
                submission_id = result.get("submission_id")
                if not submission_id:
                    log(f"No submission_id for {detail.get('title')}: {str(result)[:80]}")
                    continue

                status = await check_result(submission_id)
                log(f"({submitted+1}/{num_problems}) {detail.get('title')} ({detail.get('difficulty')}) [{lang}] -> {status}")

                if status == "Accepted":
                    submitted += 1
                    success = True
                    newly_solved.add(slug)
                    consecutive_errors = 0
                    if slug == daily_slug:
                        state["last_daily_date"] = today
                else:
                    log(f"Got {status} on {detail.get('title')} — moving to next problem")
                    # Mark daily as attempted so it doesn't block every run
                    if slug == daily_slug:
                        state["last_daily_date"] = today
                    await asyncio.sleep(random.randint(60, 90))

                if not success:
                    log(f"Skipping {detail.get('title')}")

            except Exception as e:
                err = str(e)
                log(f"Error on {problem.get('title', problem.get('titleSlug', ''))}: {err}", "error")
                if "session" in err.lower() or "403" in err or "redirect" in err.lower() or "empty" in err.lower():
                    consecutive_errors += 1
                    if consecutive_errors >= 3:
                        log("3 consecutive session errors — stopping run. Update LEETCODE_SESSION on Render.", "error")
                        break
                    log(f"Session error, waiting 3 minutes before retrying...", "error")
                    await asyncio.sleep(180)
                else:
                    consecutive_errors = 0
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
