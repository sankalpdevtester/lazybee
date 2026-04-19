import httpx
import asyncio
import random
import os
from app.services.gemini_service import _ask, MODEL_SMALL

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
      ) { questions: data { titleSlug title difficulty } }
    }
    """
    data = await _gql(query, {"limit": limit, "filters": {"difficulty": difficulty}})
    return data.get("data", {}).get("problemsetQuestionList", {}).get("questions", [])

async def get_already_attempted() -> set:
    """Returns all recently attempted slugs (AC and non-AC)."""
    query = """
    query($username: String!) {
      recentSubmissionList(username: $username, limit: 100) { titleSlug }
      recentAcSubmissionList(username: $username, limit: 100) { titleSlug }
    }
    """
    data = await _gql(query, {"username": LEETCODE_USERNAME})
    recent = data.get("data", {}).get("recentSubmissionList", []) or []
    ac = data.get("data", {}).get("recentAcSubmissionList", []) or []
    return {s["titleSlug"] for s in recent + ac}

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
- Slightly verbose, not clever one-liners
- Must be CORRECT and pass all test cases
- No markdown, return raw code only"""
    return _ask(prompt, model=MODEL_SMALL)

async def submit_solution(slug: str, question_id: str, code: str, lang: str = "python3") -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"https://leetcode.com/problems/{slug}/submit/",
            json={"lang": lang, "question_id": question_id, "typed_code": code},
            headers=_headers(),
        )
        return r.json()

async def check_submission_result(submission_id: int) -> str:
    """Poll until submission result is ready."""
    async with httpx.AsyncClient(timeout=30) as client:
        for _ in range(15):
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

        # Load our persistent solved tracking from Redis
        lc_state = read_json("leetcode_state")
        our_solved = set(lc_state.get("solved", []))
        last_daily_date = lc_state.get("last_daily_date", "")

        # Also get recently attempted from LeetCode API
        recently_attempted = await get_already_attempted()
        skip_slugs = our_solved | recently_attempted

        log(f"Skipping {len(skip_slugs)} problems | Streak: {progress.get('streak', 0)} days")

        # Fetch problems
        easy = await get_problems("EASY", 50)
        medium = await get_problems("MEDIUM", 50)
        hard = await get_problems("HARD", 30)
        all_problems = easy + medium + hard

        # Build queue - daily first (only if not done today)
        queue = []
        if daily_slug and daily_slug not in skip_slugs and last_daily_date != today:
            daily_detail = await get_problem_detail(daily_slug)
            if daily_detail and daily_detail.get("questionId"):
                queue.append(daily_detail)
                log(f"Daily challenge: {daily_detail.get('title')}")

        # Build difficulty pools
        unsolved = [p for p in all_problems if p["titleSlug"] not in skip_slugs and p["titleSlug"] != daily_slug]
        easy_pool = [p for p in unsolved if p["difficulty"] == "Easy"]
        medium_pool = [p for p in unsolved if p["difficulty"] == "Medium"]
        hard_pool = [p for p in unsolved if p["difficulty"] == "Hard"]

        # Fallback if pools empty
        if not hard_pool:
            hard_pool = [p for p in all_problems if p["difficulty"] == "Hard" and p["titleSlug"] not in our_solved]
        if not medium_pool:
            medium_pool = [p for p in all_problems if p["difficulty"] == "Medium" and p["titleSlug"] not in our_solved]
        if not easy_pool:
            easy_pool = [p for p in all_problems if p["difficulty"] == "Easy" and p["titleSlug"] not in our_solved]

        slots = num_problems - len(queue)
        n_hard = max(1, slots // 5)
        n_medium = max(1, slots // 3)
        n_easy = max(1, slots - n_hard - n_medium)

        picks = []
        if hard_pool:
            picks += random.sample(hard_pool, min(n_hard, len(hard_pool)))
        if medium_pool:
            picks += random.sample(medium_pool, min(n_medium, len(medium_pool)))
        if easy_pool:
            picks += random.sample(easy_pool, min(n_easy, len(easy_pool)))
        random.shuffle(picks)
        queue += picks

        # Extra fallback
        if len(queue) < num_problems * 2:
            extra = [p for p in all_problems if p["titleSlug"] not in {q.get("titleSlug") for q in queue}]
            random.shuffle(extra)
            queue += extra[:num_problems * 2]

        accepted_count = 0
        session_tried = set()

        for problem in queue:
            if accepted_count >= num_problems:
                break

            slug = problem.get("titleSlug")
            if not slug or slug in session_tried:
                continue
            session_tried.add(slug)

            try:
                detail = problem if problem.get("questionId") else await get_problem_detail(slug)
                if not detail or not detail.get("questionId"):
                    continue

                if accepted_count > 0:
                    delay = random.randint(90, 300)
                    log(f"Waiting {delay}s...")
                    await asyncio.sleep(delay)

                accepted = False
                for attempt in range(2):
                    code = generate_human_like_solution(detail, "python3")
                    if not code or len(code) < 10:
                        continue

                    result = await submit_solution(slug, detail["questionId"], code, "python3")
                    submission_id = result.get("submission_id")
                    if not submission_id:
                        log(f"No submission_id for {detail.get('title')}: {str(result)[:100]}", "error")
                        break

                    status = await check_submission_result(submission_id)
                    log(f"({accepted_count+1}/{num_problems}) {detail.get('title')} ({detail.get('difficulty')}) → {status}")

                    if status == "Accepted":
                        accepted_count += 1
                        accepted = True
                        our_solved.add(slug)
                        if slug == daily_slug:
                            lc_state["last_daily_date"] = today
                        break
                    else:
                        if attempt == 0:
                            log(f"Retrying {detail.get('title')}...")
                            await asyncio.sleep(5)

                if not accepted:
                    log(f"Could not get Accepted for {detail.get('title')} - moving on")

            except Exception as e:
                log(f"Error on {problem.get('title', slug)}: {e}", "error")
                continue

        # Save solved tracking to Redis
        lc_state["solved"] = list(our_solved)
        write_json("leetcode_state", lc_state)

        log(f"Session complete: {accepted_count}/{num_problems} accepted")
        badges = await get_badges()
        log(f"Badges: {len(badges.get('earned', []))} earned | Upcoming: {[b['name'] for b in badges.get('upcoming', [])]}")

    except Exception as e:
        log(f"LeetCode run failed: {e}", "error")
