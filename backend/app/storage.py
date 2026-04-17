import json
import os
from pathlib import Path
from sqlalchemy import create_engine, Column, String, Text, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Session

DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "lazybee.db"
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})

class Base(DeclarativeBase):
    pass

class KVStore(Base):
    __tablename__ = "kvstore"
    key = Column(String, primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class LogEntry(Base):
    __tablename__ = "logs"
    id = Column(String, primary_key=True)
    timestamp = Column(String, nullable=False)
    account = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    level = Column(String, default="info")

Base.metadata.create_all(engine)

def read_json(key: str) -> dict:
    with Session(engine) as s:
        row = s.get(KVStore, key)
        if not row:
            return {}
        try:
            return json.loads(row.value)
        except Exception:
            return {}

def write_json(key: str, data: dict):
    with Session(engine) as s:
        row = s.get(KVStore, key)
        if row:
            row.value = json.dumps(data)
        else:
            s.add(KVStore(key=key, value=json.dumps(data)))
        s.commit()

def append_log(timestamp: str, account: str, message: str, level: str = "info"):
    import uuid
    with Session(engine) as s:
        s.add(LogEntry(id=str(uuid.uuid4()), timestamp=timestamp, account=account, message=message, level=level))
        s.commit()
        # Keep only last 500 logs
        count = s.query(LogEntry).count()
        if count > 500:
            oldest = s.query(LogEntry).order_by(LogEntry.timestamp.asc()).limit(count - 500).all()
            for entry in oldest:
                s.delete(entry)
            s.commit()

def get_logs(limit: int = 500) -> list:
    with Session(engine) as s:
        rows = s.query(LogEntry).order_by(LogEntry.timestamp.asc()).limit(limit).all()
        return [{"timestamp": r.timestamp, "account": r.account, "message": r.message, "level": r.level} for r in rows]
