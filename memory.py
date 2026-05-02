import json
import sqlite3
import asyncio
from datetime import datetime
from typing import Optional
from config import CONFIG
from logger import log

class Memory:
    def __init__(self, db_path=CONFIG.DATABASE_PATH):
        self.db_path = db_path
        self._lock = asyncio.Lock()
        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self):
        conn = self._get_conn()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    session_id TEXT DEFAULT 'default',
                    metadata TEXT DEFAULT '{}'
                );
                CREATE TABLE IF NOT EXISTS actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    parameters TEXT DEFAULT '{}',
                    result TEXT DEFAULT '',
                    success INTEGER DEFAULT 1,
                    thought TEXT DEFAULT '',
                    response TEXT DEFAULT ''
                );
                CREATE TABLE IF NOT EXISTS state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    category TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    confidence REAL DEFAULT 1.0
                );
                CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
            """)
            conn.commit()
            log.info("✅ База данных инициализирована")
        finally:
            conn.close()

    async def store_message(self, role, content, session_id="default", metadata=None):
        async with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    "INSERT INTO messages (timestamp, role, content, session_id, metadata) VALUES (?, ?, ?, ?, ?)",
                    (datetime.utcnow().isoformat(), role, content, session_id, json.dumps(metadata or {}))
                )
                conn.commit()
            finally:
                conn.close()

    async def get_recent_messages(self, limit=20, session_id="default"):
        async with self._lock:
            conn = self._get_conn()
            try:
                rows = conn.execute(
                    "SELECT role, content, timestamp FROM messages WHERE session_id=? ORDER BY id DESC LIMIT ?",
                    (session_id, limit)
                ).fetchall()
                return [dict(r) for r in reversed(rows)]
            finally:
                conn.close()

    async def get_message_count(self):
        async with self._lock:
            conn = self._get_conn()
            try:
                return conn.execute("SELECT COUNT(*) as cnt FROM messages").fetchone()["cnt"]
            finally:
                conn.close()

    async def clear_session(self, session_id="default"):
        async with self._lock:
            conn = self._get_conn()
            try:
                conn.execute("DELETE FROM messages WHERE session_id=?", (session_id,))
                conn.commit()
            finally:
                conn.close()

    async def set_state(self, key, value):
        async with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    "INSERT INTO state (key, value, updated_at) VALUES (?, ?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
                    (key, value, datetime.utcnow().isoformat())
                )
                conn.commit()
            finally:
                conn.close()

    async def get_state(self, key):
        async with self._lock:
            conn = self._get_conn()
            try:
                row = conn.execute("SELECT value FROM state WHERE key=?", (key,)).fetchone()
                return row["value"] if row else None
            finally:
                conn.close()

    async def store_knowledge(self, category, key, value, confidence=1.0):
        async with self._lock:
            conn = self._get_conn()
            try:
                existing = conn.execute(
                    "SELECT id FROM knowledge WHERE category=? AND key=?", (category, key)
                ).fetchone()
                if existing:
                    conn.execute(
                        "UPDATE knowledge SET value=?, timestamp=? WHERE id=?",
                        (value, datetime.utcnow().isoformat(), existing["id"])
                    )
                else:
                    conn.execute(
                        "INSERT INTO knowledge (timestamp, category, key, value, confidence) VALUES (?, ?, ?, ?, ?)",
                        (datetime.utcnow().isoformat(), category, key, value, confidence)
                    )
                conn.commit()
            finally:
                conn.close()

    async def get_knowledge(self, category=None, limit=20):
        async with self._lock:
            conn = self._get_conn()
            try:
                if category:
                    rows = conn.execute(
                        "SELECT category, key, value, confidence FROM knowledge WHERE category=? LIMIT ?",
                        (category, limit)
                    ).fetchall()
                else:
                    rows = conn.execute(
                        "SELECT category, key, value, confidence FROM knowledge ORDER BY timestamp DESC LIMIT ?",
                        (limit,)
                    ).fetchall()
                return [dict(r) for r in rows]
            finally:
                conn.close()

    async def store_action(self, action_type, parameters, result, success, thought="", response=""):
        async with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    "INSERT INTO actions (timestamp, action_type, parameters, result, success, thought, response) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (datetime.utcnow().isoformat(), action_type, json.dumps(parameters), result, 1 if success else 0, thought, response)
                )
                conn.commit()
            finally:
                conn.close()

    async def get_action_count(self):
        async with self._lock:
            conn = self._get_conn()
            try:
                return conn.execute("SELECT COUNT(*) as cnt FROM actions").fetchone()["cnt"]
            finally:
                conn.close()

    async def log_activity(self, activity_type, description):
        log.info(f"[{activity_type}] {description}")