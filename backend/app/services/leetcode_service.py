import httpx

LEETCODE_GQL = "https://leetcode.com/graphql"
LEETCODE_USERNAME = "q9hZI5XkeT"

DAILY_QUERY = """
query {
  activeDailyCodingChallengeQuestion {
    date
    link
    question {
      title
      difficulty
      topicTags { name }
      hints
    }
  }
}
"""

PROBLEM_LIST_QUERY = """
query {
  problemsetQuestionList(
    categorySlug: ""
    limit: 10
    skip: 0
    filters: {}
  ) {
    questions {
      title
      titleSlug
      difficulty
      topicTags { name }
    }
  }
}
"""

PROFILE_QUERY = """
query($username: String!) {
  matchedUser(username: $username) {
    username
    submitStats {
      acSubmissionNum {
        difficulty
        count
      }
    }
    profile {
      ranking
      reputation
    }
    userCalendar {
      streak
      totalActiveDays
    }
  }
  allQuestionsCount {
    difficulty
    count
  }
}
"""

async def fetch_daily_problem() -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.post(LEETCODE_GQL, json={"query": DAILY_QUERY})
            data = r.json()["data"]["activeDailyCodingChallengeQuestion"]
            q = data["question"]
            return {
                "title": q["title"],
                "difficulty": q["difficulty"],
                "link": f"https://leetcode.com{data['link']}",
                "tags": [t["name"] for t in q["topicTags"]],
                "hint": q["hints"][0] if q["hints"] else None,
                "date": data["date"],
            }
        except Exception as e:
            return {"error": str(e)}

async def fetch_problem_list() -> list:
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.post(LEETCODE_GQL, json={"query": PROBLEM_LIST_QUERY})
            questions = r.json()["data"]["problemsetQuestionList"]["questions"]
            return [
                {
                    "title": q["title"],
                    "difficulty": q["difficulty"],
                    "link": f"https://leetcode.com/problems/{q['titleSlug']}/",
                    "tags": [t["name"] for t in q["topicTags"]],
                }
                for q in questions
            ]
        except Exception as e:
            return [{"error": str(e)}]

async def fetch_user_profile() -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.post(LEETCODE_GQL, json={"query": PROFILE_QUERY, "variables": {"username": LEETCODE_USERNAME}})
            data = r.json()["data"]
            user = data["matchedUser"]
            stats = {s["difficulty"]: s["count"] for s in user["submitStats"]["acSubmissionNum"]}
            totals = {s["difficulty"]: s["count"] for s in data["allQuestionsCount"]}
            calendar = user.get("userCalendar") or {}
            return {
                "username": LEETCODE_USERNAME,
                "profile_url": f"https://leetcode.com/u/{LEETCODE_USERNAME}/",
                "ranking": user["profile"]["ranking"],
                "solved": {
                    "all": stats.get("All", 0),
                    "easy": stats.get("Easy", 0),
                    "medium": stats.get("Medium", 0),
                    "hard": stats.get("Hard", 0),
                },
                "total": {
                    "easy": totals.get("Easy", 0),
                    "medium": totals.get("Medium", 0),
                    "hard": totals.get("Hard", 0),
                },
                "streak": calendar.get("streak", 0),
                "active_days": calendar.get("totalActiveDays", 0),
            }
        except Exception as e:
            return {"error": str(e)}
