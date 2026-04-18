import json
import os
from upstash_redis import Redis

_redis = Redis(
    url=os.getenv("UPSTASH_REDIS_REST_URL", ""),
    token=os.getenv("UPSTASH_REDIS_REST_TOKEN", ""),
)

def read_json(key: str) -> dict:
    try:
        val = _redis.get(key)
        if not val:
            return {}
        if isinstance(val, dict):
            return val
        return json.loads(val)
    except Exception:
        return {}

def write_json(key: str, data: dict):
    try:
        _redis.set(key, json.dumps(data))
    except Exception:
        pass

def append_log(timestamp: str, account: str, message: str, level: str = "info"):
    try:
        logs = get_logs(500)
        logs.append({"timestamp": timestamp, "account": account, "message": message, "level": level})
        if len(logs) > 500:
            logs = logs[-500:]
        _redis.set("logs", json.dumps(logs))
    except Exception:
        pass

def get_logs(limit: int = 500) -> list:
    try:
        val = _redis.get("logs")
        if not val:
            return []
        logs = json.loads(val) if isinstance(val, str) else val
        return logs[-limit:]
    except Exception:
        return []

# Keep DATA_DIR for any legacy references
from pathlib import Path
DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
DATA_DIR.mkdir(exist_ok=True)
