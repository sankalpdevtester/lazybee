"""
LazyBee LeetCode Local Runner
Runs from YOUR PC so LeetCode accepts the session (Render's IP gets blocked).
Set up Windows Task Scheduler to run this 6x daily.
"""
import httpx
import asyncio
import random
import re
import os
import sys
import json
from datetime import datetime, timezone
from pathlib import Path

# ── CONFIG ──────────────────────────────────────────────────────────────────
LEETCODE_SESSION = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfYXV0aF91c2VyX2lkIjoiMjEwMTc5MTAiLCJfYXV0aF91c2VyX2JhY2tlbmQiOiJhbGxhdXRoLmFjY291bnQuYXV0aF9iYWNrZW5kcy5BdXRoZW50aWNhdGlvbkJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiI1NzY3YTI3OTBjZWRjYWI3ZjVkMWFjNThlZjM3ODQ3OTE4MzBlODY3MGFjOTM0NDIyMTA0YTA3NTRiYTE5ZDVlIiwic2Vzc2lvbl91dWlkIjoiMDFhZjQ4NGQiLCJpZCI6MjEwMTc5MTAsImVtYWlsIjoiZ3VwdGFzaGl2YWFuaTIzM0BnbWFpbC5jb20iLCJ1c2VybmFtZSI6InE5aFpJNVhrZVQiLCJ1c2VyX3NsdWciOiJxOWhaSTVYa2VUIiwiYXZhdGFyIjoiaHR0cHM6Ly9hc3NldHMubGVldGNvZGUuY29tL3VzZXJzL3E5aFpJNVhrZVQvYXZhdGFyXzE3NzE0NzMyOTgucG5nIiwicmVmcmVzaGVkX2F0IjoxNzgxMDg3OTUzLCJpcCI6IjE5My4xNDguMTYuMyIsImlkZW50aXR5IjoiOTBkYWE1NTE2MDQyNjlkYmNkY2YyMzdiNWNjNzAwZjMiLCJkZXZpY2Vfd2l0aF9pcCI6WyIxMmI3NmQ3YTlmNDE3ZjA1ZTE2NzU5MmY0OGYwMWMyZiIsIjE5My4xNDguMTYuMyJdfQ.7kTip_3avIsqrpO8sPonAQmn8lLj27sZxsHWjV0OBh0"
LEETCODE_CSRF   = "8IjQH72IxhhY2dvc42WKkhdZV7Chk4fI"
GROQ_API_KEY    = ""  # fill in from Render env vars
LEETCODE_USERNAME = "q9hZI5XkeT"
NUM_PROBLEMS    = 5
STATE_FILE      = Path(__file__).parent / "lc_local_state.json"
# ────────────────────────────────────────────────────────────────────────────

LEETCODE_GQL = "https://leetcode.com/graphql"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")

def _headers():
    return {
        "Content-Type": "application/json",
        "Cookie": f"LEETCODE_SESSION={LEETCODE_SESSION}; csrftoken={LEETCODE_CSRF}",
        "x-csrftoken": LEETCODE_CSRF,
        "Referer": "https://leetcode.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

def _load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"solved": [], "last_daily_date": ""}

def _save_state(state):
    STATE_FILE.write_text(json.dumps(state))

async def _gql(query, variables={}):
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(LEETCODE_GQL, json={"query": query, "variables": variables}, headers=_headers())
        return r.json()

async def get_problems(difficulty, limit=100):
    q = """query($limit:Int,$filters:QuestionListFilterInput){problemsetQuestionList:questionList(categorySlug:"" limit:$limit skip:0 filters:$filters){questions:data{titleSlug title difficulty}}}"""
    data = await _gql(q, {"limit": limit, "filters": {"difficulty": difficulty}})
    return data.get("data", {}).get("problemsetQuestionList", {}).get("questions", [])

async def get_already_solved():
    q = """query($u:String!){recentAcSubmissionList(username:$u,limit:100){titleSlug}}"""
    data = await _gql(q, {"u": LEETCODE_USERNAME})
    return {s["titleSlug"] for s in (data.get("data", {}).get("recentAcSubmissionList") or [])}

async def get_problem_detail(slug):
    q = """query($s:String!){question(titleSlug:$s){questionId title titleSlug content difficulty codeSnippets{lang langSlug code}}}"""
    data = await _gql(q, {"s": slug})
    return data.get("data", {}).get("question", {})

async def get_badge_progress():
    q = """query($u:String!){matchedUser(username:$u){submitStats{acSubmissionNum{difficulty count}}userCalendar{streak}}activeDailyCodingChallengeQuestion{date question{titleSlug title}}}"""
    data = await _gql(q, {"u": LEETCODE_USERNAME})
    user = data.get("data", {}).get("matchedUser", {})
    daily = data.get("data", {}).get("activeDailyCodingChallengeQuestion", {})
    stats = {s["difficulty"]: s["count"] for s in user.get("submitStats", {}).get("acSubmissionNum", [])}
    return {"solved": stats, "streak": user.get("userCalendar", {}).get("streak", 0), "daily_challenge": daily}

def ask_groq(prompt):
    import urllib.request
    body = json.dumps({"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}], "temperature": 0.2, "max_tokens": 4096}).encode()
    req = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions", data=body,
        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())["choices"][0]["message"]["content"]

def generate_solution(detail, lang):
    title = detail.get("title", "")
    content = (detail.get("content", "") or "")[:600]
    snippet = next((s["code"] for s in (detail.get("codeSnippets") or []) if s["langSlug"] == lang), "")
    difficulty = detail.get("difficulty", "Easy")
    code = ask_groq(f"""Solve this LeetCode {difficulty} problem in {lang}. Must pass ALL test cases, NO TLE.
Problem: {title}
{content}
Starting code: {snippet}
Rules: optimal time complexity, handle all edge cases, do NOT redefine TreeNode/ListNode, return raw code only no markdown.""")
    code = re.sub(r'^```[\w]*\n', '', code.strip())
    code = re.sub(r'\n```$', '', code.strip())
    return code.strip()

async def submit(slug, question_id, code, lang):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"https://leetcode.com/problems/{slug}/submit/",
            json={"lang": lang, "question_id": question_id, "typed_code": code},
            headers=_headers())
        if r.status_code != 200 or not r.text.strip():
            raise RuntimeError(f"Submit failed: HTTP {r.status_code} body={r.text[:100]}")
        return r.json()

async def check_result(submission_id):
    async with httpx.AsyncClient(timeout=60) as client:
        for _ in range(20):
            await asyncio.sleep(3)
            try:
                r = await client.get(f"https://leetcode.com/submissions/detail/{submission_id}/check/", headers=_headers())
                if r.status_code != 200: continue
                data = r.json()
                state = data.get("state", "")
                if state == "SUCCESS": return data.get("status_msg", "Unknown")
                if state in ("PENDING", "STARTED"): continue
                return state or "Unknown"
            except: continue
    return "Timeout"

async def run():
    if not GROQ_API_KEY:
        log("ERROR: Set GROQ_API_KEY in this script")
        return

    log(f"Starting LeetCode session — targeting {NUM_PROBLEMS} accepted")
    state = _load_state()
    persistent_solved = set(state.get("solved", []))

    progress = await get_badge_progress()
    daily = progress.get("daily_challenge", {})
    daily_slug = daily.get("question", {}).get("titleSlug") if daily else None
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    api_solved = await get_already_solved()
    all_solved = persistent_solved | api_solved
    log(f"Solved: {len(all_solved)} total | Streak: {progress.get('streak', 0)} days")

    easy   = await get_problems("EASY",   100)
    medium = await get_problems("MEDIUM", 100)
    hard   = await get_problems("HARD",    50)

    queue = []
    if daily_slug and state.get("last_daily_date") != today and daily_slug not in all_solved:
        d = await get_problem_detail(daily_slug)
        if d and d.get("questionId"):
            queue.append(d)
            log(f"Daily: {d.get('title')}")

    unsolved = [p for p in (easy + medium + hard) if p["titleSlug"] not in all_solved and p["titleSlug"] != daily_slug]
    random.shuffle(unsolved)
    queue += [p for p in unsolved if p["difficulty"] == "Easy"]
    queue += [p for p in unsolved if p["difficulty"] == "Medium"]
    queue += [p for p in unsolved if p["difficulty"] == "Hard"]
    log(f"Queue: {len(queue)} unsolved")

    submitted = 0
    newly_solved = set()

    for problem in queue:
        if submitted >= NUM_PROBLEMS:
            break
        try:
            slug = problem.get("titleSlug")
            if not slug: continue
            detail = problem if problem.get("questionId") else await get_problem_detail(slug)
            if not detail or not detail.get("questionId"): continue
            if not detail.get("codeSnippets"): log(f"Skipping locked: {detail.get('title', slug)}"); continue

            if submitted > 0:
                delay = random.randint(60, 120)
                log(f"Waiting {delay}s...")
                await asyncio.sleep(delay)

            snippets = detail.get("codeSnippets") or []
            available = [s["langSlug"] for s in snippets]
            lang = "mysql" if "mysql" in available and "python3" not in available else \
                   "bash"  if "bash"  in available and "python3" not in available else "python3"

            for attempt in range(3):
                code = generate_solution(detail, lang)
                if not code or len(code) < 10: continue
                result = await submit(slug, detail["questionId"], code, lang)
                sid = result.get("submission_id")
                if not sid:
                    log(f"No submission_id: {str(result)[:80]}")
                    await asyncio.sleep(10)
                    continue
                status = await check_result(sid)
                log(f"({submitted+1}/{NUM_PROBLEMS}) {detail.get('title')} [{detail.get('difficulty')}] [{lang}] -> {status}")
                if status == "Accepted":
                    submitted += 1
                    newly_solved.add(slug)
                    if slug == daily_slug:
                        state["last_daily_date"] = today
                    break
                elif attempt < 2:
                    log(f"Got {status}, retrying...")
                    await asyncio.sleep(5)
            else:
                log(f"Skipping {detail.get('title')} after 3 attempts")

        except Exception as e:
            log(f"Error on {problem.get('title', problem.get('titleSlug', ''))}: {e}")

    if newly_solved:
        state["solved"] = list(persistent_solved | api_solved | newly_solved)
        _save_state(state)
        log(f"Saved {len(newly_solved)} new solved (total: {len(state['solved'])})")
    log(f"Done: {submitted}/{NUM_PROBLEMS} accepted")

if __name__ == "__main__":
    asyncio.run(run())
