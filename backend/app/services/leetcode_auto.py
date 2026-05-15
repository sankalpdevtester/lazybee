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
      recentAcSubmissionList(username: $username, limit: 1000) { titleSlug }
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

def generate_human_like_solution(problem: dict) -> tuple:
    title = problem.get("title", "")
    content = (problem.get("content", "") or "")[:600]
    difficulty = problem.get("difficulty", "Easy")
    snippets = problem.get("codeSnippets") or []

    # Auto-detect language - SQL/Shell problems don't have python3
    available_langs = [s["langSlug"] for s in snippets]
    if "mysql" in available_langs and "python3" not in available_langs:
        lang = "mysql"
    elif "bash" in available_langs and "python3" not in available_langs:
        lang = "bash"
    else:
        lang = "python3"

    snippet = next((s["code"] for s in snippets if s["langSlug"] == lang), "")

    prompt = f"""Solve this LeetCode {difficulty} problem in {lang}.
Problem: {title}
{content}

Code template:
{snippet}

Rules:
- Return ONLY the raw code, no markdown, no backticks, no explanation
- Must be 100% correct and pass all test cases
- Do NOT redefine TreeNode, ListNode or any provided classes"""

    code = _ask(prompt)
    code = re.sub(r'^```[\w]*\n', '', code.strip())
    code = re.sub(r'\n```$', '', code.strip())
    return code.strip(), lang

async def submit_solution(slug: str, question_id: str, code: str, lang: str = "python3") -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"https://leetcode.com/problems/{slug}/submit/",
            json={"lang": lang, "question_id": question_id, "typed_code": code},
            headers=_headers(),
        )
        return r.json()

async def check_submission_result(submission_id: int) -> str:
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

async def run_daily_leetcode(num_problems: int = 8):
    from app.storage import append_log, read_json, write_json
    from datetime import datetime

    def log(msg, level="info"):
        append_log(datetime.utcnow().isoformat(), "leetcode", msg, level)

    try:
        progress = await get_badge_progress()
        daily = progress.get("daily_challenge", {})
        daily_slug = daily.get("question", {}).get("titleSlug") if daily else None
        today = datetime.utcnow().strftime("%Y-%m-%d")

        lc_state = read_json("leetcode_state")
        last_daily_date = lc_state.get("last_daily_date", "")
        redis_solved = set(lc_state.get("solved", []))
        lc_ac = await get_already_solved()
        all_solved = lc_ac | redis_solved

        log(f"Solved: {len(all_solved)} | Streak: {progress.get('streak', 0)} days")

        # Fetch problems
        easy = await get_problems("EASY", 100)
        medium = await get_problems("MEDIUM", 100)
        hard = await get_problems("HARD", 50)
        all_problems = easy + medium + hard

        # Build queue starting with daily
        queue = []
        if daily_slug and last_daily_date != today and daily_slug not in all_solved:
            d = await get_problem_detail(daily_slug)
            if d and d.get("questionId"):
                queue.append(d)
                log(f"Daily: {d.get('title')}")

        # Add unsolved problems
        unsolved = [p for p in all_problems if p["titleSlug"] not in all_solved and p["titleSlug"] != daily_slug]
        easy_u = [p for p in unsolved if p["difficulty"] == "Easy"]
        med_u = [p for p in unsolved if p["difficulty"] == "Medium"]
        hard_u = [p for p in unsolved if p["difficulty"] == "Hard"]

        slots = num_problems - len(queue)
        n_hard = max(1, slots // 5)
        n_med = max(1, slots // 3)
        n_easy = max(1, slots - n_hard - n_med)

        picks = []
        if hard_u: picks += random.sample(hard_u, min(n_hard, len(hard_u)))
        if med_u: picks += random.sample(med_u, min(n_med, len(med_u)))
        if easy_u: picks += random.sample(easy_u, min(n_easy, len(easy_u)))
        random.shuffle(picks)
        queue += picks

        # Pad with more unsolved
        used = {q.get("titleSlug") for q in queue}
        extra = [p for p in unsolved if p["titleSlug"] not in used]
        random.shuffle(extra)
        queue += extra[:num_problems * 3]

        # Last resort - any problem
        if len(queue) < num_problems * 2:
            used = {q.get("titleSlug") for q in queue}
            fallback = [p for p in all_problems if p["titleSlug"] not in used]
            random.shuffle(fallback)
            queue += fallback[:num_problems * 2]

        log(f"Queue: {len(queue)} available, need {num_problems} accepted")

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
                    delay = random.randint(60, 180)
                    log(f"Waiting {delay}s...")
                    await asyncio.sleep(delay)

                success = False
                for attempt in range(3):
                    code, detected_lang = generate_human_like_solution(detail)
                    if not code or len(code) < 10:
                        log(f"Empty code for {detail.get('title')}", "error")
                        continue

                    result = await submit_solution(slug, detail["questionId"], code, detected_lang)
                    submission_id = result.get("submission_id")
                    if not submission_id:
                        log(f"No submission_id for {detail.get('title')}: {str(result)[:100]}", "error")
                        break

                    status = await check_submission_result(submission_id)
                    log(f"({submitted+1}/{num_problems}) {detail.get('title')} ({detail.get('difficulty')}) [{detected_lang}] -> {status}")

                    if status == "Accepted":
                        submitted += 1
                        success = True
                        redis_solved.add(slug)
                        if slug == daily_slug:
                            lc_state["last_daily_date"] = today
                        break
                    else:
                        if attempt < 2:
                            log(f"Got {status}, retrying...")
                            await asyncio.sleep(3)

                if not success:
                    log(f"Skipping {detail.get('title')} after 3 attempts")

            except Exception as e:
                log(f"Error on {problem.get('title', slug)}: {e}", "error")
                continue

        lc_state["solved"] = list(redis_solved)
        write_json("leetcode_state", lc_state)
        log(f"Session done: {submitted}/{num_problems} accepted")
        badges = await get_badges()
        log(f"Badges: {len(badges.get('earned', []))} earned | Upcoming: {[b['name'] for b in badges.get('upcoming', [])]}")

    except Exception as e:
        log(f"LeetCode run failed: {e}", "error")
