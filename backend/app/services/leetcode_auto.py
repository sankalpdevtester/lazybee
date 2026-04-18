import httpx
import asyncio
import random
import os
from app.services.gemini_service import _ask

LEETCODE_GQL = "https://leetcode.com/graphql"
LEETCODE_SESSION = os.getenv("LEETCODE_SESSION", "")
CSRF_TOKEN = os.getenv("LEETCODE_CSRF", "")

HEADERS = {
    "Content-Type": "application/json",
    "Cookie": f"LEETCODE_SESSION={LEETCODE_SESSION}; csrftoken={CSRF_TOKEN}",
    "x-csrftoken": CSRF_TOKEN,
    "Referer": "https://leetcode.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

LANG_MAP = {
    "python3": "python3",
    "javascript": "javascript",
    "cpp": "cpp",
}

async def _gql(query: str, variables: dict = {}) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(LEETCODE_GQL, json={"query": query, "variables": variables}, headers=HEADERS)
        return r.json()

async def get_easy_problems(limit: int = 20) -> list:
    query = """
    query($limit: Int) {
      problemsetQuestionList(categorySlug: "" limit: $limit skip: 0 filters: {difficulty: EASY}) {
        questions { titleSlug title difficulty }
      }
    }
    """
    data = await _gql(query, {"limit": limit})
    return data.get("data", {}).get("problemsetQuestionList", {}).get("questions", [])

async def get_problem_detail(slug: str) -> dict:
    query = """
    query($titleSlug: String!) {
      question(titleSlug: $titleSlug) {
        questionId title titleSlug content difficulty
        codeSnippets { lang langSlug code }
        exampleTestcaseList
      }
    }
    """
    data = await _gql(query, {"titleSlug": slug})
    return data.get("data", {}).get("question", {})

async def get_already_solved() -> set:
    query = """
    query {
      userAcSubmissionList(limit: 100 offset: 0) {
        submissions { titleSlug }
      }
    }
    """
    data = await _gql(query)
    subs = data.get("data", {}).get("userAcSubmissionList", {}).get("submissions", [])
    return {s["titleSlug"] for s in subs}

def generate_human_like_solution(problem: dict, lang: str = "python3") -> str:
    title = problem.get("title", "")
    content = problem.get("content", "")[:800]
    snippet = next((s["code"] for s in problem.get("codeSnippets", []) if s["langSlug"] == lang), "")

    prompt = f"""
Write a solution for this LeetCode problem in {lang}.

Problem: {title}
Description: {content}
Starting code: {snippet}

Rules for making it look human-written:
- Use simple variable names like i, j, n, res, temp, curr
- Add 1-2 minor inefficiencies (like an extra variable that's not needed)
- Add 1-2 casual comments like # check this or # handle edge case
- Avoid overly clever one-liners
- Make it slightly verbose, like a student would write
- Introduce one small redundant check or condition
- DO NOT use advanced built-ins or library tricks
- Must still be CORRECT and pass all test cases

Return ONLY the raw code, no explanation, no markdown.
"""
    return _ask(prompt)

async def submit_solution(slug: str, code: str, lang: str = "python3") -> dict:
    detail = await get_problem_detail(slug)
    question_id = detail.get("questionId")
    test_cases = detail.get("exampleTestcaseList", [])

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"https://leetcode.com/problems/{slug}/submit/",
            json={
                "lang": lang,
                "question_id": question_id,
                "typed_code": code,
            },
            headers=HEADERS,
        )
        result = r.json()
        return result

async def run_daily_leetcode(num_problems: int = 5):
    from app.storage import append_log
    from datetime import datetime

    def log(msg, level="info"):
        append_log(datetime.utcnow().isoformat(), "leetcode", msg, level)

    try:
        problems = await get_easy_problems(50)
        solved = await get_already_solved()

        # Filter out already solved
        unsolved = [p for p in problems if p["titleSlug"] not in solved]
        if not unsolved:
            log("All easy problems already solved")
            return

        # Pick random problems
        to_solve = random.sample(unsolved, min(num_problems, len(unsolved)))

        for i, problem in enumerate(to_solve):
            try:
                slug = problem["titleSlug"]
                detail = await get_problem_detail(slug)
                if not detail:
                    continue

                # Generate human-like solution
                code = generate_human_like_solution(detail, "python3")
                if not code:
                    continue

                # Random delay between submissions (2-8 minutes) to look human
                if i > 0:
                    delay = random.randint(120, 480)
                    log(f"Waiting {delay}s before next submission...")
                    await asyncio.sleep(delay)

                result = await submit_solution(slug, code, "python3")
                submission_id = result.get("submission_id")
                log(f"Submitted: {problem['title']} - submission_id: {submission_id}")

            except Exception as e:
                log(f"Failed to submit {problem.get('title', slug)}: {e}", "error")
                continue

    except Exception as e:
        log(f"LeetCode daily run failed: {e}", "error")
