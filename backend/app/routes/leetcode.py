from fastapi import APIRouter, Depends
from app.routes.deps import require_auth
from app.services.leetcode_service import fetch_daily_problem, fetch_problem_list, fetch_user_profile
from app.services.leetcode_auto import get_badges, get_badge_progress

router = APIRouter()

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
