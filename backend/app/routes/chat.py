from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.routes.deps import require_auth
from app.storage import read_json, get_logs
from app.services.gemini_service import chat_with_context

router = APIRouter()

class MessageBody(BaseModel):
    message: str

@router.post("/", dependencies=[Depends(require_auth)])
def chat(body: MessageBody):
    state = read_json("rotation")
    projects = state.get("projects", {})
    logs = get_logs(5)
    slot0 = projects.get(state.get("slot_0", ""), {})
    slot1 = projects.get(state.get("slot_1", ""), {})

    context = f"""
Current app state:
- Automation account: sankalpdevtester only
- Active project slot 0: {slot0.get('title', 'none')} (day {slot0.get('day', 0)}/28)
- Active project slot 1: {slot1.get('title', 'none')} (day {slot1.get('day', 0)}/28)
- Current slot: {state.get('current_slot', 0)}
- Recent log: {logs[-1]['message'] if logs else 'no activity yet'}
"""
    reply = chat_with_context(body.message, context)
    return {"reply": reply}

@router.delete("/history", dependencies=[Depends(require_auth)])
def clear_history():
    return {"message": "Chat history cleared."}
