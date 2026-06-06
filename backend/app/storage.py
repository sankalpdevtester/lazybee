import json
import os
from pathlib import Path

DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
DATA_DIR.mkdir(exist_ok=True)

# --- Redis: lazy init, only if credentials are set ---
_redis = None

def _get_redis():
    global _redis
    if _redis is not None:
        return _redis
    url = os.getenv("UPSTASH_REDIS_REST_URL", "")
    token = os.getenv("UPSTASH_REDIS_REST_TOKEN", "")
    if not url or not token:
        return None
    try:
        from upstash_redis import Redis
        _redis = Redis(url=url, token=token)
        return _redis
    except Exception:
        return None

# --- Local JSON fallback ---
def _local_path(key: str) -> Path:
    return DATA_DIR / f"{key}.json"

def _local_read(key: str) -> dict:
    p = _local_path(key)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}

def _local_write(key: str, data: dict):
    _local_path(key).write_text(json.dumps(data))

# --- Public API ---
def read_json(key: str) -> dict:
    r = _get_redis()
    if r:
        try:
            val = r.get(key)
            if not val:
                return {}
            return val if isinstance(val, dict) else json.loads(val)
        except Exception:
            pass
    return _local_read(key)

def write_json(key: str, data: dict):
    r = _get_redis()
    if r:
        try:
            r.set(key, json.dumps(data))
            return
        except Exception:
            pass
    _local_write(key, data)

def append_log(timestamp: str, account: str, message: str, level: str = "info"):
    logs = get_logs(500)
    logs.append({"timestamp": timestamp, "account": account, "message": message, "level": level})
    if len(logs) > 500:
        logs = logs[-500:]
    r = _get_redis()
    if r:
        try:
            r.set("logs", json.dumps(logs))
            return
        except Exception:
            pass
    _local_write("logs", {"logs": logs})

def get_logs(limit: int = 500) -> list:
    r = _get_redis()
    if r:
        try:
            val = r.get("logs")
            if val:
                logs = val if isinstance(val, list) else json.loads(val)
                return logs[-limit:] if isinstance(logs, list) else []
        except Exception:
            pass
    data = _local_read("logs")
    logs = data if isinstance(data, list) else data.get("logs", [])
    return logs[-limit:]
