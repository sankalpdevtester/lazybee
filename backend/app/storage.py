import json
import os
from pathlib import Path

DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))

def read_json(filename: str) -> dict:
    path = DATA_DIR / filename
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)

def write_json(filename: str, data: dict):
    DATA_DIR.mkdir(exist_ok=True)
    with open(DATA_DIR / filename, "w") as f:
        json.dump(data, f, indent=2)
