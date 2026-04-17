import bcrypt
import jwt
import os
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from app.storage import read_json, write_json
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
router = APIRouter()

JWT_SECRET = os.getenv("JWT_SECRET", "changeme")
LOCKOUT_ATTEMPTS = 5
LOCKOUT_MINUTES = 15

class PinBody(BaseModel):
    pin: str

def _auth_data():
    return read_json("auth")

def _is_registered():
    return bool(_auth_data().get("pin_hash"))

def _check_lockout(data: dict):
    attempts = data.get("failed_attempts", 0)
    lockout_until = data.get("lockout_until")
    if lockout_until:
        if datetime.utcnow().isoformat() < lockout_until:
            raise HTTPException(status_code=429, detail="Too many attempts. Try later.")
    return attempts

@router.get("/status")
def registration_status():
    return {"registered": _is_registered()}

@router.post("/register")
def register(body: PinBody):
    if _is_registered():
        raise HTTPException(status_code=403, detail="Already registered.")
    if len(body.pin) < 10:
        raise HTTPException(status_code=400, detail="PIN must be at least 10 characters.")
    hashed = bcrypt.hashpw(body.pin.encode(), bcrypt.gensalt()).decode()
    write_json("auth", {"pin_hash": hashed, "failed_attempts": 0, "lockout_until": None})
    return {"message": "Registered successfully."}

@router.post("/login")
def login(body: PinBody, request: Request):
    data = _auth_data()
    if not _is_registered():
        raise HTTPException(status_code=403, detail="Not registered yet.")
    attempts = _check_lockout(data)
    if not bcrypt.checkpw(body.pin.encode(), data["pin_hash"].encode()):
        attempts += 1
        lockout_until = None
        if attempts >= LOCKOUT_ATTEMPTS:
            lockout_until = (datetime.utcnow() + timedelta(minutes=LOCKOUT_MINUTES)).isoformat()
            attempts = 0
        write_json("auth", {**data, "failed_attempts": attempts, "lockout_until": lockout_until})
        raise HTTPException(status_code=401, detail="Invalid PIN.")
    write_json("auth", {**data, "failed_attempts": 0, "lockout_until": None})
    token = jwt.encode({"sub": "owner", "exp": datetime.utcnow() + timedelta(days=30)}, JWT_SECRET, algorithm="HS256")
    return {"token": token}
