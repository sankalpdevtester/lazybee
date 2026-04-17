from fastapi import APIRouter, Depends
from app.routes.deps import require_auth
from app.services.leetcode_service import fetch_daily_problem, fetch_problem_list, fetch_user_profile

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
