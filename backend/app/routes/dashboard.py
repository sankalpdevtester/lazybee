from fastapi import APIRouter, Depends
from app.routes.deps import require_auth
from app.storage import read_json, get_logs
from app.services.leetcode_service import fetch_daily_problem

router = APIRouter()

@router.get("/", dependencies=[Depends(require_auth)])
async def dashboard():
    accounts_data = read_json("accounts")
    accounts = [{"username": a["username"], "active": a.get("active", True)} for a in accounts_data.get("accounts", [])]
    rotation = read_json("rotation")
    logs = get_logs(10)
    leetcode = await fetch_daily_problem()

    return {
        "accounts": accounts,
        "rotation": rotation,
        "recent_logs": logs,
        "leetcode_daily": leetcode,
    }

@router.post("/run-now", dependencies=[Depends(require_auth)])
def run_now():
    from app.scheduler.jobs import _get_token, _get_state, _save_state, _create_new_project, _continue_project, _next_language, _projects_this_month, BLOCKED_REPOS
    import threading
    def _run():
        token = _get_token()
        if not token:
            return
        state = _get_state()
        projects = state.get("projects", {})
        # Force slot 0 - bypass day of week check
        slot_key = "slot_0"
        slot_project_name = state.get(slot_key)
        project = projects.get(slot_project_name) if slot_project_name else None
        if not project or slot_project_name in BLOCKED_REPOS:
            _create_new_project(token, state, projects, 0, slot_key)
        else:
            _continue_project(token, state, projects, slot_project_name)
    threading.Thread(target=_run, daemon=True).start()
    return {"message": "GitHub automation triggered. Check logs for progress."}

@router.post("/run-leetcode", dependencies=[Depends(require_auth)])
def run_leetcode():
    import threading, asyncio
    from app.services.leetcode_auto import run_daily_leetcode
    def _run():
        asyncio.run(run_daily_leetcode(8))
    threading.Thread(target=_run, daemon=True).start()
    return {"message": "LeetCode automation triggered. Solving 8 problems. Check logs."}
