from fastapi import APIRouter, Depends
from app.routes.deps import require_auth
from app.storage import read_json
from app.services.leetcode_service import fetch_daily_problem

router = APIRouter()

@router.get("/", dependencies=[Depends(require_auth)])
async def dashboard():
    accounts_data = read_json("accounts.json")
    accounts = [{"username": a["username"], "active": a.get("active", True)} for a in accounts_data.get("accounts", [])]
    rotation = read_json("rotation.json")
    logs = read_json("logs.json").get("logs", [])[-10:]
    leetcode = await fetch_daily_problem()

    return {
        "accounts": accounts,
        "rotation": rotation,
        "recent_logs": logs,
        "leetcode_daily": leetcode,
    }
