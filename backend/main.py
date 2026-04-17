import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routes import auth, github, leetcode, dashboard, chat
from app.scheduler.jobs import start_scheduler
from app.storage import read_json, write_json, DATA_DIR

DEFAULT_ACCOUNTS = [
    {"username": "Shivaani-spec", "token": "", "active": True, "display_only": True},
    {"username": "PirateKingLuffie", "token": "", "active": True, "display_only": True},
    {"username": "liveinsaaninsaan", "token": "", "active": True, "display_only": True},
    {"username": "sankalpdevtester", "token": os.getenv("SANKALPDEVTESTER_TOKEN", ""), "active": True, "display_only": False},
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    _migrate_json_to_db()
    _seed_accounts()
    start_scheduler()
    yield

def _seed_accounts():
    """Always ensure accounts are present - survives redeployments."""
    data = read_json("accounts")
    existing = {a["username"]: a for a in data.get("accounts", [])}
    for acc in DEFAULT_ACCOUNTS:
        if acc["username"] not in existing:
            existing[acc["username"]] = acc
        else:
            # Update token from env in case it changed, keep other settings
            if not acc["display_only"] and acc["token"]:
                existing[acc["username"]]["token"] = acc["token"]
    write_json("accounts", {"accounts": list(existing.values())})

def _migrate_json_to_db():
    """One-time migration of existing JSON files into SQLite."""
    import json
    from pathlib import Path
    for filename in ["auth.json", "accounts.json", "rotation.json"]:
        path = DATA_DIR / filename
        if path.exists():
            try:
                data = json.loads(path.read_text())
                key = filename.replace(".json", "")
                write_json(key, data)
                path.rename(path.with_suffix(".json.migrated"))
            except Exception:
                pass
app = FastAPI(lifespan=lifespan)

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth")
app.include_router(github.router, prefix="/api/github")
app.include_router(leetcode.router, prefix="/api/leetcode")
app.include_router(chat.router, prefix="/api/chat")
app.include_router(dashboard.router, prefix="/api/dashboard")
