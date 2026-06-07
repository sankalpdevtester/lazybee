from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.routes.deps import require_auth
from app.storage import read_json, write_json
from app.services.linkedin_content import run_linkedin_post, generate_linkedin_post
import os, threading, asyncio
from datetime import datetime

router = APIRouter()

class PostBody(BaseModel):
    type: str = "daily_update"

class ScheduleBody(BaseModel):
    type: str
    scheduled_for: str  # ISO date string
    content: str = ""   # if empty, auto-generate at post time

class EditBody(BaseModel):
    content: str

@router.get("/status")
def linkedin_status():
    token = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
    return {
        "connected": bool(token),
        "error": None if token else "LINKEDIN_ACCESS_TOKEN not set in Render env vars",
    }

@router.get("/history", dependencies=[Depends(require_auth)])
def get_history():
    data = read_json("linkedin_history")
    return data.get("posts", [])

@router.get("/scheduled", dependencies=[Depends(require_auth)])
def get_scheduled():
    data = read_json("linkedin_scheduled")
    return data.get("posts", [])

@router.post("/schedule", dependencies=[Depends(require_auth)])
def schedule_post(body: ScheduleBody):
    data = read_json("linkedin_scheduled")
    posts = data.get("posts", [])
    post = {
        "id": f"sched_{datetime.utcnow().timestamp()}",
        "type": body.type,
        "scheduled_for": body.scheduled_for,
        "content": body.content,
        "status": "pending",
    }
    posts.append(post)
    write_json("linkedin_scheduled", {"posts": posts})
    return {"message": "Post scheduled.", "post": post}

@router.delete("/scheduled/{post_id}", dependencies=[Depends(require_auth)])
def delete_scheduled(post_id: str):
    data = read_json("linkedin_scheduled")
    posts = [p for p in data.get("posts", []) if p["id"] != post_id]
    write_json("linkedin_scheduled", {"posts": posts})
    return {"message": "Deleted."}

@router.patch("/scheduled/{post_id}", dependencies=[Depends(require_auth)])
def edit_scheduled(post_id: str, body: EditBody):
    data = read_json("linkedin_scheduled")
    posts = data.get("posts", [])
    for p in posts:
        if p["id"] == post_id:
            p["content"] = body.content
    write_json("linkedin_scheduled", {"posts": posts})
    return {"message": "Updated."}

@router.post("/preview", dependencies=[Depends(require_auth)])
def preview_post(body: PostBody):
    """Generate a post preview without actually posting it."""
    rotation = read_json("rotation")
    projects = rotation.get("projects", {})
    slot0 = projects.get(rotation.get("slot_0", ""), {})
    lc_state = read_json("leetcode_state")
    context = {
        "active_project": slot0,
        "github_projects": list(projects.values())[:5],
        "leetcode_solved_today": lc_state.get("solved_today", 0),
        "leetcode_streak": 0,
        "total_solved": len(lc_state.get("solved", [])),
    }
    content = generate_linkedin_post(body.type, context)
    return {"content": content, "char_count": len(content)}

@router.post("/post-now", dependencies=[Depends(require_auth)])
def post_now(body: PostBody):
    """Post immediately to LinkedIn."""
    def _run():
        asyncio.run(run_linkedin_post(body.type))
    threading.Thread(target=_run, daemon=True).start()
    return {"message": f"Posting [{body.type}] to LinkedIn. Check logs."}
