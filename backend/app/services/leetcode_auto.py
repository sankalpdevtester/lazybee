import httpx
import asyncio
import random
import os
from app.services.gemini_service import generate_leetcode_solution

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

async def get_ac_submissions() -> set:
    """Only returns ACCEPTED submissions - don't skip failed ones."""
    query = """
    query($username: String!) {
      recentAcSubmissionList(username: $username, limit: 100) { titleSlug }
    }
    """
    data = await _gql(query, {"username": LEETCODE_USERNAME})
    ac = data.get("data", {}).get("recentAcSubmissionList", []) or []
    return {s["titleSlug"] for s in ac}

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

        # Only skip problems we've ACCEPTED - don't skip failed ones
        lc_state = read_json("leetcode_state")
        our_accepted = set(lc_state.get("solved", []))
        last_daily_date = lc_state.get("last_daily_date", "")

        # Also skip recently AC'd from LeetCode directly
        lc_ac = await get_ac_submissions()
        skip_slugs = our_accepted | lc_ac

        solved_stats = progress.get("solved", {})
        log(f"Total solved: Easy={solved_stats.get('Easy',0)} Medium={solved_stats.get('Medium',0)} Hard={solved_stats.get('Hard',0)} | Streak: {progress.get('streak',0)} days")

        # Fetch all problems
        easy = await get_problems("EASY", 100)
        medium = await get_problems("MEDIUM", 100)
        hard = await get_problems("HARD", 50)
        all_problems = easy + medium + hard

        log(f"Available: {len(easy)} easy, {len(medium)} medium, {len(hard)} hard | Skipping {len(skip_slugs)} already solved")

        # Build queue - daily first (only once per day)
        queue = []
        if daily_slug and last_daily_date != today:
            daily_detail = await get_problem_detail(daily_slug)
            if daily_detail and daily_detail.get("questionId"):
                queue.append(daily_detail)
                log(f"Daily challenge added: {daily_detail.get('title')} ({daily_detail.get('difficulty')})")

        # Build pools - only skip accepted ones, not failed attempts
        easy_pool = [p for p in easy if p["titleSlug"] not in skip_slugs and p["titleSlug"] != daily_slug]
        medium_pool = [p for p in medium if p["titleSlug"] not in skip_slugs and p["titleSlug"] != daily_slug]
        hard_pool = [p for p in hard if p["titleSlug"] not in skip_slugs and p["titleSlug"] != daily_slug]

        log(f"Unsolved pools: {len(easy_pool)} easy, {len(medium_pool)} medium, {len(hard_pool)} hard")

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

        # Shuffle non-daily problems
        daily_item = queue[0] if queue and queue[0].get("titleSlug") == daily_slug else None
        rest = [q for q in queue if q.get("titleSlug") != daily_slug]
        random.shuffle(rest)
        queue = ([daily_item] if daily_item else []) + rest

        # Pad with more problems if needed
        while len(queue) < num_problems * 3:
            extra = [p for p in all_problems if p["titleSlug"] not in {q.get("titleSlug") for q in queue} and p["titleSlug"] not in skip_slugs]
            if not extra:
                extra = [p for p in all_problems if p["titleSlug"] not in {q.get("titleSlug") for q in queue}]
            if not extra:
                break
            random.shuffle(extra)
            queue += extra[:5]

        log(f"Queue built: {len(queue)} problems to try, need {num_problems} accepted")

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
                    delay = random.randint(60, 240)
                    log(f"Waiting {delay}s before next...")
                    await asyncio.sleep(delay)

                difficulty = detail.get("difficulty", "Easy")
                max_tries = 3 if difficulty in ("Easy", "Medium") else 2
                accepted = False

                for attempt in range(max_tries):
                    code = generate_leetcode_solution(detail, difficulty, "python3")
                    if not code or len(code) < 10:
                        log(f"Empty code generated for {detail.get('title')}", "error")
                        continue

                    result = await submit_solution(slug, detail["questionId"], code, "python3")
                    submission_id = result.get("submission_id")
                    if not submission_id:
                        log(f"No submission_id for {detail.get('title')}: {str(result)[:150]}", "error")
                        break

                    status = await check_submission_result(submission_id)
                    log(f"[{accepted_count+1}/{num_problems}] {detail.get('title')} ({difficulty}) → {status}")

                    if status == "Accepted":
                        accepted_count += 1
                        accepted = True
                        our_accepted.add(slug)
                        if slug == daily_slug:
                            lc_state["last_daily_date"] = today
                        break
                    else:
                        if attempt < max_tries - 1:
                            log(f"Got {status}, regenerating solution (attempt {attempt+2}/{max_tries})...")
                            await asyncio.sleep(3)

                if not accepted:
                    log(f"Moving on from {detail.get('title')} after {max_tries} attempts")

            except Exception as e:
                log(f"Error on {problem.get('title', slug)}: {e}", "error")
                continue

        lc_state["solved"] = list(our_accepted)
        write_json("leetcode_state", lc_state)

        log(f"✅ Session done: {accepted_count}/{num_problems} accepted")
        badges = await get_badges()
        log(f"Badges: {len(badges.get('earned', []))} earned | Upcoming: {[b['name'] for b in badges.get('upcoming', [])]}")

    except Exception as e:
        log(f"LeetCode run failed: {e}", "error")
