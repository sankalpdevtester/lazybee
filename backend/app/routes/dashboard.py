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
    from app.scheduler.jobs import run_daily_automation
    import threading
    threading.Thread(target=run_daily_automation, daemon=True).start()
    return {"message": "GitHub automation triggered. Check logs for progress."}

@router.post("/run-leetcode", dependencies=[Depends(require_auth)])
def run_leetcode():
    import threading, asyncio
    from app.services.leetcode_auto import run_daily_leetcode
    def _run():
        asyncio.run(run_daily_leetcode(8))
    threading.Thread(target=_run, daemon=True).start()
    return {"message": "LeetCode automation triggered. Solving 8 problems. Check logs."}
