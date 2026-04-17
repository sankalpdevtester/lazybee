from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.routes.deps import require_auth
from app.storage import read_json, write_json
from app.services.github_service import get_account_stats, get_all_repos, get_contribution_graph, get_languages

router = APIRouter()

class AccountBody(BaseModel):
    username: str
    token: str

@router.get("/accounts", dependencies=[Depends(require_auth)])
def list_accounts():
    data = read_json("accounts.json")
    accounts = data.get("accounts", [])
    return [{"username": a["username"], "active": a.get("active", True)} for a in accounts]

@router.post("/accounts", dependencies=[Depends(require_auth)])
def add_account(body: AccountBody):
    data = read_json("accounts.json")
    accounts = data.get("accounts", [])
    if any(a["username"] == body.username for a in accounts):
        return {"message": "Account already exists."}
    accounts.append({"username": body.username, "token": body.token, "active": True})
    write_json("accounts.json", {"accounts": accounts})
    return {"message": "Account added."}

@router.delete("/accounts/{username}", dependencies=[Depends(require_auth)])
def remove_account(username: str):
    data = read_json("accounts.json")
    accounts = [a for a in data.get("accounts", []) if a["username"] != username]
    write_json("accounts.json", {"accounts": accounts})
    return {"message": "Account removed."}

@router.patch("/accounts/{username}/toggle", dependencies=[Depends(require_auth)])
def toggle_account(username: str):
    data = read_json("accounts.json")
    accounts = data.get("accounts", [])
    for a in accounts:
        if a["username"] == username:
            a["active"] = not a.get("active", True)
    write_json("accounts.json", {"accounts": accounts})
    return {"message": "Toggled."}

@router.get("/stats", dependencies=[Depends(require_auth)])
async def all_stats():
    import asyncio
    data = read_json("accounts.json")
    accounts = data.get("accounts", [])
    results = await asyncio.gather(
        *[get_account_stats(a["username"], a["token"]) for a in accounts],
        return_exceptions=True
    )
    return [r if not isinstance(r, Exception) else {"error": str(r)} for r in results]

@router.get("/repos/{username}", dependencies=[Depends(require_auth)])
async def repos(username: str):
    data = read_json("accounts.json")
    account = next((a for a in data.get("accounts", []) if a["username"] == username), None)
    if not account:
        return []
    return await get_all_repos(account["username"], account["token"])

@router.get("/profile/{username}", dependencies=[Depends(require_auth)])
async def profile(username: str):
    data = read_json("accounts.json")
    account = next((a for a in data.get("accounts", []) if a["username"] == username), None)
    if not account:
        return {"error": "Account not found"}
    token = account.get("token", "")
    stats = await get_account_stats(username, token)
    graph = await get_contribution_graph(username, token)
    repos = await get_all_repos(username, token)
    languages = await get_languages(username, token)
    return {"stats": {**stats, "languages": languages}, "graph": graph, "repos": repos, "display_only": account.get("display_only", False)}

@router.get("/logs", dependencies=[Depends(require_auth)])
def get_logs():
    return read_json("logs.json").get("logs", [])
