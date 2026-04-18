import os
import threading
import time
import httpx
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routes import auth, github, leetcode, dashboard, chat
from app.scheduler.jobs import start_scheduler
from app.storage import read_json, write_json, DATA_DIR

DEFAULT_ACCOUNTS = [
    {"username": "Shivaani-spec", "token": os.getenv("SHIVAANI_TOKEN", ""), "active": True, "display_only": True},
    {"username": "PirateKingLuffie", "token": os.getenv("PIRATE_TOKEN", ""), "active": True, "display_only": True},
    {"username": "liveinsaaninsaan", "token": os.getenv("LIVE_TOKEN", ""), "active": True, "display_only": True},
    {"username": "sankalpdevtester", "token": os.getenv("SANKALPDEVTESTER_TOKEN", ""), "active": True, "display_only": False},
]

def _seed_accounts():
    data = read_json("accounts")
    existing = {a["username"]: a for a in data.get("accounts", [])}
    for acc in DEFAULT_ACCOUNTS:
        if acc["username"] not in existing:
            existing[acc["username"]] = acc
        else:
            if not acc["display_only"] and acc["token"]:
                existing[acc["username"]]["token"] = acc["token"]
    write_json("accounts", {"accounts": list(existing.values())})

def _start_self_ping():
    def ping():
        while True:
            time.sleep(270)
            try:
                httpx.get("https://lazybee.onrender.com", timeout=10)
            except Exception:
                pass
    threading.Thread(target=ping, daemon=True).start()

@asynccontextmanager
async def lifespan(app: FastAPI):
    _seed_accounts()
    start_scheduler()
    _start_self_ping()
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth")
app.include_router(github.router, prefix="/api/github")
app.include_router(leetcode.router, prefix="/api/leetcode")
app.include_router(chat.router, prefix="/api/chat")
app.include_router(dashboard.router, prefix="/api/dashboard")

@app.get("/")
@app.head("/")
def health():
    return {"status": "ok"}
