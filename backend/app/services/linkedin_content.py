from app.services.gemini_service import _ask
from app.storage import read_json, write_json, append_log
from datetime import datetime

def _log(msg, level="info"):
    append_log(datetime.utcnow().isoformat(), "linkedin", msg, level)

def generate_linkedin_post(post_type: str, context: dict) -> str:
    github_projects = context.get("github_projects", [])
    leetcode_solved = context.get("leetcode_solved_today", 0)
    leetcode_streak = context.get("leetcode_streak", 0)
    active_project = context.get("active_project", {})
    scheduled_posts = context.get("scheduled", [])

    if post_type == "daily_update":
        prompt = f"""Write a LinkedIn post for a software developer's daily update.

Facts to include (use what's relevant, ignore empty ones):
- LeetCode problems solved today: {leetcode_solved}
- LeetCode streak: {leetcode_streak} days
- Active GitHub project: {active_project.get('title', '')} ({active_project.get('language', '')}) - day {active_project.get('day', 0)}
- Recent GitHub projects: {', '.join([p.get('title','') for p in github_projects[:3]])}

Style rules:
- Sound like a real developer, not a corporate bot
- 3-5 short paragraphs max
- No cringe phrases like "Excited to share" or "Thrilled to announce"
- Use 2-3 relevant emojis max
- End with 3-4 hashtags like #Python #OpenSource #100DaysOfCode
- Keep it under 1300 characters
- Be specific about what was actually built/solved, not vague

Return only the post text, nothing else."""

    elif post_type == "project_launch":
        prompt = f"""Write a LinkedIn post announcing a new open source project.

Project details:
- Name: {active_project.get('title', '')}
- Description: {active_project.get('description', '')}
- Stack: {active_project.get('stack', active_project.get('language', ''))}
- Features: {', '.join(active_project.get('features', [])[:5])}
- GitHub URL: {active_project.get('repo_url', '')}

Style rules:
- Sound excited but genuine, like a real dev sharing their work
- Mention the tech stack
- Include what problem it solves
- End with GitHub link and 3-4 hashtags
- Under 1300 characters
- No corporate buzzwords

Return only the post text, nothing else."""

    elif post_type == "leetcode_milestone":
        prompt = f"""Write a LinkedIn post about a LeetCode milestone.

Facts:
- Total problems solved: {context.get('total_solved', 0)}
- Current streak: {leetcode_streak} days
- Problems today: {leetcode_solved}

Style rules:
- Genuine developer voice, not bragging
- Mention what was learned or a specific challenge
- Under 800 characters
- 2-3 hashtags: #LeetCode #DSA #CodingChallenge

Return only the post text, nothing else."""

    else:
        prompt = f"""Write a LinkedIn post for a software developer.
Topic: {post_type}
Context: {context}
Style: genuine developer voice, under 1300 characters, 3-4 hashtags.
Return only the post text."""

    return _ask(prompt)


async def run_linkedin_post(post_type: str = "daily_update"):
    from app.storage import read_json, write_json
    from app.services.linkedin_service import get_profile, post_text
    import os

    token = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
    if not token:
        _log("SKIPPED: LINKEDIN_ACCESS_TOKEN not set", "error")
        return

    try:
        # Build context from current state
        rotation = read_json("rotation")
        projects = rotation.get("projects", {})
        slot0 = projects.get(rotation.get("slot_0", ""), {})
        lc_state = read_json("leetcode_state")
        solved_list = lc_state.get("solved", [])

        context = {
            "active_project": slot0,
            "github_projects": list(projects.values())[:5],
            "leetcode_solved_today": lc_state.get("solved_today", 0),
            "leetcode_streak": 0,
            "total_solved": len(solved_list),
        }

        # Generate post content
        post_text_content = generate_linkedin_post(post_type, context)
        if not post_text_content or len(post_text_content) < 20:
            _log("Post generation returned empty", "error")
            return

        # Get LinkedIn person URN
        profile = await get_profile()
        person_urn = profile.get("sub", "")
        if not person_urn:
            _log("Could not get LinkedIn person URN", "error")
            return

        # Post it
        result = await post_text(person_urn, post_text_content)
        post_id = result.get("id", "unknown")

        # Save to history
        history = read_json("linkedin_history")
        posts = history.get("posts", [])
        posts.append({
            "id": post_id,
            "type": post_type,
            "content": post_text_content,
            "posted_at": datetime.utcnow().isoformat(),
        })
        write_json("linkedin_history", {"posts": posts[-50:]})  # keep last 50

        _log(f"Posted [{post_type}]: {post_text_content[:80]}...")

    except Exception as e:
        _log(f"LinkedIn post failed: {e}", "error")
