from fastapi import APIRouter, Depends
from app.routes.deps import require_auth
from app.services.leetcode_service import fetch_daily_problem, fetch_problem_list, fetch_user_profile
from app.services.leetcode_auto import get_badges, get_badge_progress, _check_auth
import os

router = APIRouter()

@router.get("/status", dependencies=[Depends(require_auth)])
def leetcode_status():
    """Check if LeetCode credentials are configured and valid."""
    auth_err = _check_auth()
    groq_ok = bool(os.getenv("GROQ_API_KEY", ""))
    return {
        "session_set": not auth_err,
        "groq_set": groq_ok,
        "ready": auth_err is None and groq_ok,
        "error": auth_err if auth_err else ("GROQ_API_KEY not set" if not groq_ok else None),
        "fix": "Update LEETCODE_SESSION and LEETCODE_CSRF from your browser cookies at leetcode.com, and set GROQ_API_KEY in .env" if (auth_err or not groq_ok) else None,
    }

@router.get("/daily", dependencies=[Depends(require_auth)])
async def daily_problem():
    return await fetch_daily_problem()

@router.get("/problems", dependencies=[Depends(require_auth)])
async def problem_list():
    return await fetch_problem_list()

@router.get("/profile", dependencies=[Depends(require_auth)])
async def user_profile():
    return await fetch_user_profile()

@router.get("/badges", dependencies=[Depends(require_auth)])
async def badges():
    b = await get_badges()
    p = await get_badge_progress()
    return {**b, **p}

@router.post("/seed-solved", dependencies=[Depends(require_auth)])
async def seed_solved():
    """Manually seed all solved problems from LC API into Redis."""
    from app.storage import read_json, write_json
    from app.services.leetcode_auto import get_already_solved
    lc_ac = await get_already_solved()
    state = read_json("leetcode_state")
    existing = set(state.get("solved", []))
    merged = existing | lc_ac
    state["solved"] = list(merged)
    write_json("leetcode_state", state)
    return {"message": f"Seeded {len(merged)} solved problems into Redis ({len(lc_ac)} from LC API, {len(existing)} already saved)"}
