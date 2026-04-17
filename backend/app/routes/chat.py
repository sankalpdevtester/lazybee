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
    rotation = read_json("rotation")
    accounts_data = read_json("accounts")
    accounts = [a["username"] for a in accounts_data.get("accounts", [])]
    logs = get_logs(5)

    context = f"""
Current app state:
- Linked GitHub accounts: {', '.join(accounts) if accounts else 'none yet'}
- Current rotation index: {rotation.get('current_index', 0)}
- Active projects: {list(rotation.get('projects', {}).keys())}
- Recent log: {logs[-1]['message'] if logs else 'no activity yet'}
"""
    reply = chat_with_context(body.message, context)
    return {"reply": reply}

@router.delete("/history", dependencies=[Depends(require_auth)])
def clear_history():
    return {"message": "Chat history cleared."}
