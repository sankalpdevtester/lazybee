import httpx
import asyncio
import random
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
        categorySlug: ""
        limit: $limit
        skip: 0
        filters: $filters
      ) {
        questions: data {
          titleSlug
          title
          difficulty
        }
      }
    }
    """
    data = await _gql(query, {"limit": limit, "filters": {"difficulty": difficulty}})
    return data.get("data", {}).get("problemsetQuestionList", {}).get("questions", [])

async def get_already_solved() -> set:
    query = """
    query($username: String!) {
      recentAcSubmissionList(username: $username, limit: 100) {
        titleSlug
      }
    }
    """
    data = await _gql(query, {"username": LEETCODE_USERNAME})
    subs = data.get("data", {}).get("recentAcSubmissionList", []) or []
    return {s["titleSlug"] for s in subs}

async def get_problem_detail(slug: str) -> dict:
    query = """
    query($titleSlug: String!) {
      question(titleSlug: $titleSlug) {
        questionId
        title
        titleSlug
        content
        difficulty
        codeSnippets { lang langSlug code }
      }
    }
    """
    data = await _gql(query, {"titleSlug": slug})
    return data.get("data", {}).get("question", {})

def generate_human_like_solution(problem: dict, lang: str = "python3") -> str:
    title = problem.get("title", "")
    content = (problem.get("content", "") or "")[:600]
    snippet = next((s["code"] for s in (problem.get("codeSnippets") or []) if s["langSlug"] == lang), "")
    prompt = f"""
Write a solution for this LeetCode problem in {lang}.
Problem: {title}
Description: {content}
Starting code: {snippet}

Make it look like a student wrote it:
- Simple variable names (i, j, n, res, temp)
- 1-2 casual comments like # handle edge case or # check boundary
- Slightly verbose, not clever one-liners
- One small redundant check is fine
- Must be CORRECT and pass all test cases
- No markdown, return raw code only
"""
    return _ask(prompt)

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

async def run_daily_leetcode(num_problems: int = 5):
    from app.storage import append_log
    from datetime import datetime

    def log(msg, level="info"):
        append_log(datetime.utcnow().isoformat(), "leetcode", msg, level)

    try:
        # Get mix of easy and medium problems
        easy = await get_problems("EASY", 50)
        medium = await get_problems("MEDIUM", 30)
        all_problems = easy + medium

        solved = await get_already_solved()
        log(f"Already solved {len(solved)} problems recently")

        unsolved = [p for p in all_problems if p["titleSlug"] not in solved]
        if not unsolved:
            # If all solved recently, just pick random ones anyway
            unsolved = all_problems
            log("Picking from all problems since recent list is full")

        to_solve = random.sample(unsolved, min(num_problems, len(unsolved)))

        for i, problem in enumerate(to_solve):
            try:
                slug = problem["titleSlug"]
                detail = await get_problem_detail(slug)
                if not detail or not detail.get("questionId"):
                    log(f"Skipping {slug} - no detail", "error")
                    continue

                code = generate_human_like_solution(detail, "python3")
                if not code or len(code) < 10:
                    log(f"Skipping {slug} - empty code", "error")
                    continue

                if i > 0:
                    delay = random.randint(120, 480)
                    log(f"Waiting {delay}s before next submission...")
                    await asyncio.sleep(delay)

                result = await submit_solution(slug, code, "python3")
                submission_id = result.get("submission_id", "unknown")
                log(f"Submitted: {problem['title']} ({problem['difficulty']}) - id: {submission_id}")

            except Exception as e:
                log(f"Failed {problem.get('title', slug)}: {e}", "error")
                continue

    except Exception as e:
        log(f"LeetCode daily run failed: {e}", "error")
