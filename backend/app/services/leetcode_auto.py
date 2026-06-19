import httpx
import asyncio
import random
import re
import os
from app.services.gemini_service import _ask

LEETCODE_GQL = "https://leetcode.com/graphql"
LEETCODE_USERNAME = "q9hZI5XkeT"

def _headers():
    return {
        "Content-Type": "application/json",
        "Cookie": f"LEETCODE_SESSION={os.getenv('LEETCODE_SESSION','').strip()}; csrftoken={os.getenv('LEETCODE_CSRF','').strip()}",
        "x-csrftoken": os.getenv("LEETCODE_CSRF", "").strip(),
        "Referer": "https://leetcode.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

async def _proxy(method: str, url: str, json_body=None) -> httpx.Response:
    """All LeetCode requests go through Cloudflare proxy if set, else direct."""
    proxy_url = os.getenv("LEETCODE_PROXY_URL", "").strip()
    proxy_secret = os.getenv("LEETCODE_PROXY_SECRET", "").strip()
    async with httpx.AsyncClient(timeout=30) as client:
        if proxy_url and proxy_secret:
            r = await client.post(
                proxy_url,
                json={"url": url, "method": method, "headers": _headers(), "data": json_body},
                headers={"X-Proxy-Secret": proxy_secret, "Content-Type": "application/json"},
            )
        elif method == "GET":
            r = await client.get(url, headers=_headers())
        else:
            r = await client.post(url, json=json_body, headers=_headers())

        # Auto-refresh session if LeetCode returns a new cookie
        new_session = None
        set_cookie = r.headers.get("set-cookie", "")
        if "LEETCODE_SESSION=" in set_cookie:
            import re as _re
            m = _re.search(r'LEETCODE_SESSION=([^;]+)', set_cookie)
            if m:
                new_session = m.group(1)
        if new_session and new_session != os.getenv("LEETCODE_SESSION", ""):
            _update_render_session(new_session)
        return r

def _update_render_session(new_session: str):
    """Update LEETCODE_SESSION on Render via API so it auto-refreshes."""
    render_api_key = os.getenv("RENDER_API_KEY", "").strip()
    service_id = os.getenv("RENDER_SERVICE_ID", "").strip()
    if not render_api_key or not service_id:
        # Fallback: just update in-process env so current run uses it
        os.environ["LEETCODE_SESSION"] = new_session
        return
    try:
        import httpx as _httpx
        # Get current env vars
        r = _httpx.get(
            f"https://api.render.com/v1/services/{service_id}/env-vars",
            headers={"Authorization": f"Bearer {render_api_key}", "Accept": "application/json"},
            timeout=10
        )
        if r.status_code != 200:
            os.environ["LEETCODE_SESSION"] = new_session
            return
        env_vars = r.json()
        # Find and update LEETCODE_SESSION
        updated = []
        for ev in env_vars:
            if ev.get("envVar", {}).get("key") == "LEETCODE_SESSION":
                updated.append({"key": "LEETCODE_SESSION", "value": new_session})
            else:
                updated.append({"key": ev["envVar"]["key"], "value": ev["envVar"]["value"]})
        _httpx.put(
            f"https://api.render.com/v1/services/{service_id}/env-vars",
            headers={"Authorization": f"Bearer {render_api_key}", "Accept": "application/json", "Content-Type": "application/json"},
            json=updated,
            timeout=10
        )
        os.environ["LEETCODE_SESSION"] = new_session
    except Exception:
        os.environ["LEETCODE_SESSION"] = new_session

async def _gql(query: str, variables: dict = {}) -> dict:
    r = await _proxy("POST", LEETCODE_GQL, {"query": query, "variables": variables})
    try:
        return r.json()
    except Exception:
        return {}

async def get_badge_progress() -> dict:
    data = await _gql("""query($u:String!){
      matchedUser(username:$u){submitStats{acSubmissionNum{difficulty count}}userCalendar{streak}}
      activeDailyCodingChallengeQuestion{date question{titleSlug title difficulty}}
    }""", {"u": LEETCODE_USERNAME})
    user = data.get("data", {}).get("matchedUser", {})
    daily = data.get("data", {}).get("activeDailyCodingChallengeQuestion", {})
    stats = {s["difficulty"]: s["count"] for s in user.get("submitStats", {}).get("acSubmissionNum", [])}
    return {"solved": stats, "streak": user.get("userCalendar", {}).get("streak", 0), "daily_challenge": daily}

async def get_badges() -> dict:
    data = await _gql("""query($u:String!){matchedUser(username:$u){badges{id name icon displayName}upcomingBadges{name icon}}}""", {"u": LEETCODE_USERNAME})
    user = data.get("data", {}).get("matchedUser", {})
    return {"earned": user.get("badges", []), "upcoming": user.get("upcomingBadges", [])}

async def get_problems(difficulty: str, limit: int = 100) -> list:
    data = await _gql("""query($limit:Int,$filters:QuestionListFilterInput){
      problemsetQuestionList:questionList(categorySlug:"" limit:$limit skip:0 filters:$filters){
        questions:data{titleSlug title difficulty isPaidOnly}}}""",
        {"limit": limit, "filters": {"difficulty": difficulty}})
    questions = data.get("data", {}).get("problemsetQuestionList", {}).get("questions", [])
    # Filter out premium problems right at the source
    return [q for q in questions if not q.get("isPaidOnly")]

async def get_already_solved() -> set:
    data = await _gql("""query($u:String!){recentAcSubmissionList(username:$u,limit:100){titleSlug}}""", {"u": LEETCODE_USERNAME})
    return {s["titleSlug"] for s in (data.get("data", {}).get("recentAcSubmissionList") or [])}

async def get_problem_detail(slug: str) -> dict:
    data = await _gql("""query($s:String!){question(titleSlug:$s){
      questionId title titleSlug difficulty isPaidOnly
      codeSnippets{lang langSlug code}}}""", {"s": slug})
    return data.get("data", {}).get("question", {}) or {}

def _clean_code(code: str) -> str:
    code = code.strip()
    code = re.sub(r'^```[\w]*\n?', '', code)
    code = re.sub(r'\n?```$', '', code)
    return code.strip()

def solve(problem: dict, lang: str, attempt: int = 1, prev_status: str = "") -> str:
    title = problem.get("title", "")
    content = (problem.get("content", "") or "")[:1200]
    snippet = next((s["code"] for s in (problem.get("codeSnippets") or []) if s["langSlug"] == lang), "")
    difficulty = problem.get("difficulty", "Easy")

    retry_note = ""
    if attempt == 2:
        retry_note = f"\nIMPORTANT: A previous attempt got '{prev_status}'. Think step-by-step about edge cases and reconsider your algorithm entirely. Do NOT repeat the same approach.\n"
    elif attempt >= 3:
        retry_note = f"\nIMPORTANT: Two previous attempts failed with '{prev_status}'. This is your final attempt. Use a well-known textbook algorithm that is proven correct. Prioritize correctness over cleverness.\n"

    code = _ask(f"""Solve this LeetCode {difficulty} problem in {lang}. The solution MUST be 100% correct and pass ALL test cases.
{retry_note}
Problem: {title}
{content}

Starting code:
{snippet}

Rules:
- Return ONLY raw code, no markdown, no explanation, no comments
- Use the most efficient CORRECT algorithm — think carefully about correctness first
- Handle ALL edge cases: empty input, single element, duplicates, negatives, maximum constraints
- For Hard problems use proven optimal algorithms (e.g. DP with memoization, two pointers, binary search, segment tree, BFS/DFS, merge sort)
- Do NOT redefine TreeNode, ListNode or any class already provided
- Every line of code must be correct Python3 syntax
- The code must produce the correct output for every possible input""")
    return _clean_code(code)

async def run_daily_leetcode(num_problems: int = 10):
    from app.storage import append_log, read_json, write_json
    from datetime import datetime

    def log(msg, level="info"):
        append_log(datetime.utcnow().isoformat(), "leetcode", msg, level)

    if not os.getenv("LEETCODE_SESSION", "").strip():
        log("SKIPPED: LEETCODE_SESSION not set", "error"); return
    if not os.getenv("LEETCODE_CSRF", "").strip():
        log("SKIPPED: LEETCODE_CSRF not set", "error"); return
    if not os.getenv("GROQ_API_KEY", "").strip():
        log("SKIPPED: GROQ_API_KEY not set", "error"); return

    proxy = os.getenv("LEETCODE_PROXY_URL", "").strip()
    log(f"Proxy: {'ACTIVE -> ' + proxy[:50] if proxy else 'DISABLED'}")

    try:
        progress = await get_badge_progress()
        daily = progress.get("daily_challenge", {})
        daily_slug = daily.get("question", {}).get("titleSlug") if daily else None
        today = datetime.utcnow().strftime("%Y-%m-%d")

        state = read_json("leetcode_state")
        persistent = set(state.get("solved", []))
        api_solved = await get_already_solved()
        all_solved = persistent | api_solved
        log(f"Solved: {len(all_solved)} | Streak: {progress.get('streak', 0)} days")

        easy   = await get_problems("EASY",   500)
        medium = await get_problems("MEDIUM", 500)
        hard   = await get_problems("HARD",   200)

        # Build queue: skip already solved, skip today's daily (avoid repeated WA)
        # Prioritize Easy > Medium > Hard to maximize acceptance rate
        attempted_daily = state.get("last_daily_date", "") == today
        queue = []
        if daily_slug and not attempted_daily and daily_slug not in all_solved:
            d = await get_problem_detail(daily_slug)
            if d and d.get("questionId") and not d.get("isPaidOnly"):
                queue.append(d)
                log(f"Daily: {d.get('title')}")

        unsolved = [p for p in (easy + medium + hard)
                    if p["titleSlug"] not in all_solved and p["titleSlug"] != daily_slug]
        random.shuffle(unsolved)
        queue += unsolved  # use ALL unsolved, no cap

        log(f"Queue: {len(queue)} problems, targeting {num_problems} accepted")

        submitted = 0
        newly_solved = set()

        for problem in queue:
            if submitted >= num_problems:
                break

            slug = problem.get("titleSlug", "")
            if not slug:
                continue

            try:
                detail = problem if problem.get("questionId") else await get_problem_detail(slug)
                if not detail or not detail.get("questionId"):
                    continue
                if detail.get("isPaidOnly"):
                    log(f"Skipping premium: {detail.get('title', slug)}")
                    continue

                snippets = detail.get("codeSnippets") or []
                available = [s["langSlug"] for s in snippets]

                # Skip problems with no python3 — SQL/shell 403 harder from server
                if "python3" not in available:
                    log(f"Skipping non-python: {detail.get('title', slug)}")
                    continue

                lang = "python3"

                # Wait between submissions - longer to avoid rate limiting
                if submitted > 0:
                    wait = random.randint(180, 240)
                    log(f"Waiting {wait}s...")
                    await asyncio.sleep(wait)
                else:
                    await asyncio.sleep(random.randint(10, 20))

                # Try up to 3 times with increasingly forceful prompts
                accepted = False
                last_status = ""
                for attempt in range(1, 4):
                    code = solve(detail, lang, attempt=attempt, prev_status=last_status)
                    if not code or len(code) < 10:
                        log(f"Empty solution attempt {attempt} for {detail.get('title')}, skipping")
                        break

                    r = await _proxy("POST", f"https://leetcode.com/problems/{slug}/submit/",
                        {"lang": lang, "question_id": detail["questionId"], "typed_code": code})

                    if r.status_code == 403:
                        log(f"403 on {detail.get('title')} — rate limited, waiting 3min", "error")
                        await asyncio.sleep(180)
                        break
                    if not r.text.strip() or r.status_code not in (200, 201):
                        log(f"Bad response {r.status_code} for {detail.get('title')}", "error")
                        break

                    result = r.json()
                    submission_id = result.get("submission_id")
                    if not submission_id:
                        log(f"No submission_id for {detail.get('title')}: {str(result)[:80]}")
                        break

                    # Poll result
                    status = "Timeout"
                    for _ in range(20):
                        await asyncio.sleep(3)
                        try:
                            check_r = await _proxy("GET", f"https://leetcode.com/submissions/detail/{submission_id}/check/")
                            if check_r.status_code != 200:
                                continue
                            data = check_r.json()
                            s = data.get("state", "")
                            if s == "SUCCESS":
                                status = data.get("status_msg", "Unknown")
                                break
                            if s in ("PENDING", "STARTED"):
                                continue
                            status = s or "Unknown"
                            break
                        except Exception:
                            continue

                    last_status = status
                    log(f"({submitted+1}/{num_problems}) {detail.get('title')} [{detail.get('difficulty')}] attempt {attempt} -> {status}")

                    if status == "Accepted":
                        accepted = True
                        break
                    # Retry on WA/TLE — wait before re-generating
                    if attempt < 3:
                        await asyncio.sleep(random.randint(45, 90))

                if accepted:
                    submitted += 1
                    newly_solved.add(slug)
                    if slug == daily_slug:
                        state["last_daily_date"] = today
                else:
                    # All 3 attempts failed — mark as attempted, never retry
                    if slug == daily_slug:
                        state["last_daily_date"] = today
                    newly_solved.add(slug)
                    await asyncio.sleep(random.randint(60, 90))

            except Exception as e:
                log(f"Error on {slug}: {e}", "error")
                await asyncio.sleep(30)
                continue

        if newly_solved:
            state["solved"] = list(persistent | api_solved | newly_solved)
            write_json("leetcode_state", state)
            log(f"Saved {len(newly_solved)} new (total: {len(state['solved'])})")
        elif state.get("last_daily_date") == today:
            write_json("leetcode_state", state)

        log(f"Done: {submitted}/{num_problems} accepted")
        badges = await get_badges()
        log(f"Badges: {len(badges.get('earned',[]))} earned | Upcoming: {[b['name'] for b in badges.get('upcoming',[])]}")

    except Exception as e:
        log(f"LeetCode run failed: {e}", "error")
