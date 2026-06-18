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
        # Auto-refresh session cookie
        set_cookie = r.headers.get("set-cookie", "")
        if "LEETCODE_SESSION=" in set_cookie:
            m = re.search(r'LEETCODE_SESSION=([^;]+)', set_cookie)
            if m:
                new_session = m.group(1)
                if new_session != os.getenv("LEETCODE_SESSION", ""):
                    os.environ["LEETCODE_SESSION"] = new_session
        return r

async def _gql(query: str, variables: dict = {}) -> dict:
    r = await _proxy("POST", LEETCODE_GQL, {"query": query, "variables": variables})
    try:
        return r.json()
    except Exception:
        return {}

async def get_all_problems(skip: int = 0, limit: int = 500) -> list:
    """Fetch a batch of problems from LeetCode."""
    data = await _gql("""
    query($skip:Int,$limit:Int){
      problemsetQuestionList:questionList(
        categorySlug:"" limit:$limit skip:$skip filters:{}
      ){
        total
        questions:data{titleSlug title difficulty isPaidOnly}
      }
    }""", {"skip": skip, "limit": limit})
    ql = data.get("data", {}).get("problemsetQuestionList", {})
    return ql.get("questions") or [], ql.get("total", 0)

async def get_all_free_problems() -> list:
    """Fetch ALL free python-solvable problems from LeetCode (up to 4000)."""
    all_problems = []
    skip = 0
    limit = 500
    while True:
        problems, total = await get_all_problems(skip, limit)
        if not problems:
            break
        free = [p for p in problems if not p.get("isPaidOnly")]
        all_problems.extend(free)
        skip += limit
        if skip >= total or skip >= 4000:
            break
        await asyncio.sleep(1)
    return all_problems

async def get_already_solved() -> set:
    data = await _gql("""query($u:String!){recentAcSubmissionList(username:$u,limit:100){titleSlug}}""",
        {"u": LEETCODE_USERNAME})
    return {s["titleSlug"] for s in (data.get("data", {}).get("recentAcSubmissionList") or [])}

async def get_problem_detail(slug: str) -> dict:
    data = await _gql("""query($s:String!){question(titleSlug:$s){
      questionId title titleSlug difficulty isPaidOnly
      codeSnippets{lang langSlug code}}}""", {"s": slug})
    return data.get("data", {}).get("question", {}) or {}

async def get_badge_progress() -> dict:
    data = await _gql("""query($u:String!){
      matchedUser(username:$u){submitStats{acSubmissionNum{difficulty count}}userCalendar{streak}}
      activeDailyCodingChallengeQuestion{date question{titleSlug title difficulty}}}""",
        {"u": LEETCODE_USERNAME})
    user = data.get("data", {}).get("matchedUser", {})
    daily = data.get("data", {}).get("activeDailyCodingChallengeQuestion", {})
    stats = {s["difficulty"]: s["count"] for s in user.get("submitStats", {}).get("acSubmissionNum", [])}
    return {"solved": stats, "streak": user.get("userCalendar", {}).get("streak", 0), "daily_challenge": daily}

async def get_badges() -> dict:
    data = await _gql("""query($u:String!){matchedUser(username:$u){badges{id name icon displayName}upcomingBadges{name icon}}}""",
        {"u": LEETCODE_USERNAME})
    user = data.get("data", {}).get("matchedUser", {})
    return {"earned": user.get("badges", []), "upcoming": user.get("upcomingBadges", [])}

def solve(problem: dict, lang: str) -> str:
    title = problem.get("title", "")
    content = (problem.get("content", "") or "")[:800]
    snippet = next((s["code"] for s in (problem.get("codeSnippets") or []) if s["langSlug"] == lang), "")
    difficulty = problem.get("difficulty", "Easy")
    code = _ask(f"""Solve this LeetCode {difficulty} problem in {lang}. Must be 100% correct, pass ALL test cases, no TLE.

Problem: {title}
{content}

Starting code:
{snippet}

Rules:
- Return ONLY raw code, no markdown, no explanation
- Use optimal time complexity
- Handle all edge cases including empty input
- Do NOT redefine TreeNode, ListNode or any provided class""")
    code = re.sub(r'^```[\w]*\n', '', code.strip())
    code = re.sub(r'\n```$', '', code.strip())
    return code.strip()

async def run_daily_leetcode(num_problems: int = 5):
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
    log(f"Proxy: {'ACTIVE' if proxy else 'DISABLED'}")

    try:
        progress = await get_badge_progress()
        daily = progress.get("daily_challenge", {})
        daily_slug = daily.get("question", {}).get("titleSlug") if daily else None
        today = datetime.utcnow().strftime("%Y-%m-%d")

        # Load persistent solved set
        state = read_json("leetcode_state")
        persistent = set(state.get("solved", []))

        # Merge with LC API (last 100 accepted)
        api_solved = await get_already_solved()
        all_solved = persistent | api_solved
        log(f"Solved: {len(all_solved)} total | Streak: {progress.get('streak', 0)} days")

        # Fetch ALL free problems from LeetCode (up to 4000)
        log("Fetching problem list...")
        all_problems = await get_all_free_problems()
        log(f"Total free problems: {len(all_problems)}")

        # Filter out solved ones
        unsolved = [p for p in all_problems if p["titleSlug"] not in all_solved]
        log(f"Unsolved: {len(unsolved)} problems available")

        # Build queue: daily first, then random mix of easy/medium (avoid hard for TLE)
        queue = []

        # Daily challenge if not done today
        attempted_daily = state.get("last_daily_date", "") == today
        if daily_slug and not attempted_daily and daily_slug not in all_solved:
            d = await get_problem_detail(daily_slug)
            if d and d.get("questionId") and not d.get("isPaidOnly"):
                snippets = d.get("codeSnippets") or []
                if any(s["langSlug"] == "python3" for s in snippets):
                    queue.append(d)
                    log(f"Daily: {d.get('title')}")

        # Prioritize Easy and Medium for higher acceptance rate
        easy_unsolved = [p for p in unsolved if p["difficulty"] == "Easy"]
        med_unsolved = [p for p in unsolved if p["difficulty"] == "Medium"]
        hard_unsolved = [p for p in unsolved if p["difficulty"] == "Hard"]

        random.shuffle(easy_unsolved)
        random.shuffle(med_unsolved)
        random.shuffle(hard_unsolved)

        # Fill queue with 60% easy, 30% medium, 10% hard — large pool
        pool = easy_unsolved[:60] + med_unsolved[:30] + hard_unsolved[:10]
        random.shuffle(pool)
        queue += pool

        log(f"Queue: {len(queue)} unsolved problems (Easy:{len(easy_unsolved)} Med:{len(med_unsolved)} Hard:{len(hard_unsolved)})")

        submitted = 0
        newly_solved = set()

        for problem in queue:
            if submitted >= num_problems:
                break

            slug = problem.get("titleSlug", "")
            if not slug:
                continue

            try:
                # Fetch full detail if not already fetched
                detail = problem if problem.get("questionId") else await get_problem_detail(slug)
                if not detail or not detail.get("questionId"):
                    continue
                if detail.get("isPaidOnly"):
                    continue

                # Only python3 problems
                snippets = detail.get("codeSnippets") or []
                if not any(s["langSlug"] == "python3" for s in snippets):
                    continue

                lang = "python3"

                # Wait between submissions
                if submitted > 0:
                    wait = random.randint(120, 180)
                    log(f"Waiting {wait}s...")
                    await asyncio.sleep(wait)
                else:
                    await asyncio.sleep(random.randint(5, 15))

                code = solve(detail, lang)
                if not code or len(code) < 10:
                    log(f"Empty solution for {detail.get('title')}, skipping")
                    continue

                # Submit
                r = await _proxy("POST", f"https://leetcode.com/problems/{slug}/submit/",
                    {"lang": lang, "question_id": detail["questionId"], "typed_code": code})

                if r.status_code == 403:
                    log(f"403 on {detail.get('title')} — waiting 3min", "error")
                    await asyncio.sleep(180)
                    continue
                if not r.text.strip() or r.status_code not in (200, 201):
                    log(f"Bad response {r.status_code} for {detail.get('title')}", "error")
                    continue

                result = r.json()
                submission_id = result.get("submission_id")
                if not submission_id:
                    log(f"No submission_id for {detail.get('title')}: {str(result)[:80]}")
                    continue

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

                log(f"({submitted+1}/{num_problems}) {detail.get('title')} [{detail.get('difficulty')}] -> {status}")

                if status == "Accepted":
                    submitted += 1
                    newly_solved.add(slug)
                    if slug == daily_slug:
                        state["last_daily_date"] = today
                else:
                    if slug == daily_slug:
                        state["last_daily_date"] = today
                    # Add to solved even on WA so we don't retry same problem
                    newly_solved.add(slug)
                    await asyncio.sleep(random.randint(60, 90))

            except Exception as e:
                log(f"Error on {slug}: {e}", "error")
                await asyncio.sleep(30)
                continue

        # Save ALL attempted problems so they're never repeated
        if newly_solved:
            state["solved"] = list(persistent | api_solved | newly_solved)
            write_json("leetcode_state", state)
            accepted = sum(1 for s in newly_solved if s in newly_solved)
            log(f"Saved {len(newly_solved)} attempted (total tracked: {len(state['solved'])})")
        elif state.get("last_daily_date") == today:
            write_json("leetcode_state", state)

        log(f"Done: {submitted}/{num_problems} accepted")
        badges = await get_badges()
        log(f"Badges: {len(badges.get('earned',[]))} earned | Upcoming: {[b['name'] for b in badges.get('upcoming',[])]}")

    except Exception as e:
        log(f"LeetCode run failed: {e}", "error")
