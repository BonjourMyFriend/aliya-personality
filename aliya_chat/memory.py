import sqlite3
import uuid
from datetime import datetime
from pathlib import Path


class Memory:
    """SQLite-backed conversation storage with auto-summarization."""

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        title TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        message_count INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
        content TEXT NOT NULL,
        sequence_number INTEGER NOT NULL,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (session_id) REFERENCES sessions(id)
    );

    CREATE INDEX IF NOT EXISTS idx_messages_session_seq
        ON messages(session_id, sequence_number);

    CREATE TABLE IF NOT EXISTS summaries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        summary_text TEXT NOT NULL,
        message_range_start INTEGER NOT NULL,
        message_range_end INTEGER NOT NULL,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (session_id) REFERENCES sessions(id)
    );

    CREATE INDEX IF NOT EXISTS idx_summaries_session
        ON summaries(session_id);

    -- 每日日程（上帝模块生成）
    CREATE TABLE IF NOT EXISTS daily_schedule (
        date TEXT PRIMARY KEY,
        wake_time TEXT NOT NULL,
        sleep_time TEXT NOT NULL,
        mood TEXT NOT NULL DEFAULT 'normal',
        work_seed_id TEXT,
        work_description TEXT,
        is_staying_up INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
    );

    -- 随机事件记录
    CREATE TABLE IF NOT EXISTS event_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        occurred_at TEXT DEFAULT (datetime('now')),
        seed_id TEXT,
        event_type TEXT,
        context TEXT,
        was_offline INTEGER DEFAULT 0,
        aliya_response TEXT
    );

    -- 关系进度
    CREATE TABLE IF NOT EXISTS relationship (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        phase INTEGER DEFAULT 1,
        first_interaction_date TEXT,
        total_conversation_turns INTEGER DEFAULT 0,
        active_days INTEGER DEFAULT 0,
        last_active_date TEXT,
        phase_updated_at TEXT
    );

    -- Aliya 的键值状态
    CREATE TABLE IF NOT EXISTS aliya_state (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TEXT DEFAULT (datetime('now'))
    );
    """

    SUMMARIZATION_PROMPT = """You are a conversation memory keeper for Aliya — a young woman engineer on a stranded spaceship, speaking with Nolan from 1000 years in the past.

CRITICAL: Your job is to remember IMPORTANT things about this conversation so Aliya can reference them in future chats.

Extract and summarize:

1. **Key Facts About Nolan** — What did Nolan tell you about himself? (name, interests, situation, questions asked)
2. **Topics Discussed** — What subjects did you talk about?
3. **Aliyan's Feelings/State** — How did Aliya seem to feel during this conversation?
4. **Things to Remember** — Facts, promises, unresolved questions, things Nolan seemed to care about

IMPORTANT RULES:
- If Nolan mentioned something about himself, ALWAYS include it
- If you discussed something specific, note it
- If Aliya shared something personal, remember it
- Keep each point very brief — 1 sentence max

Previous summary (add new info to these):
{previous_summary}

New messages:
{new_messages}

Output updated summary:"""

    def __init__(self, db_path: str | Path):
        self.db = sqlite3.connect(str(db_path), check_same_thread=False)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript(self.SCHEMA)
        self.db.commit()

    # ── Sessions ──

    def create_session(self, title: str = "Chat") -> str:
        session_id = str(uuid.uuid4())
        self.db.execute(
            "INSERT INTO sessions (id, title) VALUES (?, ?)",
            (session_id, title),
        )
        self.db.commit()
        return session_id

    def get_active_session(self) -> str | None:
        row = self.db.execute(
            "SELECT id FROM sessions WHERE is_active = 1 "
            "ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        return row[0] if row else None

    def deactivate_session(self, session_id: str):
        self.db.execute(
            "UPDATE sessions SET is_active = 0, updated_at = datetime('now') "
            "WHERE id = ?",
            (session_id,),
        )
        self.db.commit()

    # ── Messages ──

    def add_message(self, session_id: str, role: str, content: str):
        row = self.db.execute(
            "SELECT COALESCE(MAX(sequence_number), 0) FROM messages "
            "WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        next_seq = row[0] + 1
        self.db.execute(
            "INSERT INTO messages (session_id, role, content, sequence_number) "
            "VALUES (?, ?, ?, ?)",
            (session_id, role, content, next_seq),
        )
        self.db.execute(
            "UPDATE sessions SET message_count = message_count + 1, "
            "updated_at = datetime('now') WHERE id = ?",
            (session_id,),
        )
        self.db.commit()
        return next_seq

    def get_recent_messages(self, session_id: str, limit: int = 40) -> list[dict]:
        rows = self.db.execute(
            "SELECT role, content FROM messages "
            "WHERE session_id = ? ORDER BY sequence_number DESC LIMIT ?",
            (session_id, limit),
        ).fetchall()
        return [{"role": r, "content": c} for r, c in reversed(rows)]

    def get_message_char_count(self, session_id: str) -> int:
        row = self.db.execute(
            "SELECT COALESCE(SUM(LENGTH(content)), 0) FROM messages "
            "WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        return row[0]

    # ── Summaries ──

    def get_latest_summary(self, session_id: str) -> str:
        row = self.db.execute(
            "SELECT summary_text FROM summaries "
            "WHERE session_id = ? ORDER BY id DESC LIMIT 1",
            (session_id,),
        ).fetchone()
        return row[0] if row else ""

    def get_last_summarized_seq(self, session_id: str) -> int:
        row = self.db.execute(
            "SELECT message_range_end FROM summaries "
            "WHERE session_id = ? ORDER BY id DESC LIMIT 1",
            (session_id,),
        ).fetchone()
        return row[0] if row else 0

    def get_unsummarized_messages(self, session_id: str) -> list[tuple[str, str]]:
        last_seq = self.get_last_summarized_seq(session_id)
        rows = self.db.execute(
            "SELECT role, content FROM messages "
            "WHERE session_id = ? AND sequence_number > ? "
            "ORDER BY sequence_number",
            (session_id, last_seq),
        ).fetchall()
        return rows

    def store_summary(
        self,
        session_id: str,
        summary_text: str,
        range_start: int,
        range_end: int,
    ):
        self.db.execute(
            "INSERT INTO summaries "
            "(session_id, summary_text, message_range_start, message_range_end) "
            "VALUES (?, ?, ?, ?)",
            (session_id, summary_text, range_start, range_end),
        )
        self.db.commit()

    def needs_summary(self, session_id: str, threshold: int) -> bool:
        return self.get_message_char_count(session_id) > threshold

    def summarize(self, session_id: str, client, model: str, threshold: int):
        """Run summarization if needed. Uses OpenAI-compatible API."""
        if not self.needs_summary(session_id, threshold):
            return None

        new_messages = self.get_unsummarized_messages(session_id)
        if not new_messages:
            return self.get_latest_summary(session_id)

        previous = self.get_latest_summary(session_id) or "No previous summary."
        messages_text = "\n".join(
            f"{role}: {content}" for role, content in new_messages
        )

        response = client.chat.completions.create(
            model=model,
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": self.SUMMARIZATION_PROMPT.format(
                    previous_summary=previous,
                    new_messages=messages_text,
                ),
            }],
        )

        summary_text = response.choices[0].message.content or ""

        # Get range
        last_seq = self.get_last_summarized_seq(session_id)
        row = self.db.execute(
            "SELECT MIN(sequence_number), MAX(sequence_number) "
            "FROM messages WHERE session_id = ? AND sequence_number > ?",
            (session_id, last_seq),
        ).fetchone()
        range_start, range_end = row

        self.store_summary(session_id, summary_text, range_start, range_end)
        return summary_text

    # ── Context building ──

    def build_context(
        self,
        session_id: str,
        system_prompt: str,
        recent_turns: int = 20,
    ) -> tuple[str, list[dict]]:
        """Build system prompt + summary + recent messages for API call."""
        summary = self.get_latest_summary(session_id)
        recent = self.get_recent_messages(session_id, recent_turns * 2)

        full_system = system_prompt
        if summary:
            full_system += f"\n\n## Conversation Memory\n{summary}"

        return full_system, recent

    def close(self):
        # Summarize on close if needed
        self.db.close()

    # ── Daily Schedule ──

    def get_today_schedule(self, date: str) -> dict | None:
        """获取某天的日程。"""
        row = self.db.execute(
            "SELECT date, wake_time, sleep_time, mood, work_seed_id, "
            "work_description, is_staying_up "
            "FROM daily_schedule WHERE date = ?",
            (date,),
        ).fetchone()
        if not row:
            return None
        return {
            "date": row[0],
            "wake_time": row[1],
            "sleep_time": row[2],
            "mood": row[3],
            "work_seed_id": row[4],
            "work_description": row[5],
            "is_staying_up": bool(row[6]),
        }

    def save_schedule(self, date: str, schedule: dict):
        """保存一天的日程。"""
        self.db.execute(
            "INSERT OR REPLACE INTO daily_schedule "
            "(date, wake_time, sleep_time, mood, work_seed_id, "
            "work_description, is_staying_up) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                date,
                schedule["wake_time"],
                schedule["sleep_time"],
                schedule["mood"],
                schedule.get("work_seed_id"),
                schedule.get("work_description"),
                1 if schedule.get("is_staying_up") else 0,
            ),
        )
        self.db.commit()

    # ── Events ──

    def log_event(self, seed_id: str, event_type: str, context: str,
                  was_offline: bool = False):
        """记录一个随机事件。"""
        self.db.execute(
            "INSERT INTO event_log (seed_id, event_type, context, was_offline) "
            "VALUES (?, ?, ?, ?)",
            (seed_id, event_type, context, 1 if was_offline else 0),
        )
        self.db.commit()

    def get_recent_event(self) -> dict | None:
        """获取最近一条未消费的随机事件。"""
        # 获取最近 1 小时内、还没有被 aliya_response 标记的事件
        row = self.db.execute(
            "SELECT id, seed_id, event_type, context, occurred_at "
            "FROM event_log "
            "WHERE aliya_response IS NULL "
            "ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "seed_id": row[1],
            "event_type": row[2],
            "context": row[3],
            "occurred_at": row[4],
        }

    def mark_event_consumed(self, event_id: int, aliya_response: str = ""):
        """标记事件已被 Aliya 消费（说过相关的话了）。"""
        self.db.execute(
            "UPDATE event_log SET aliya_response = ? WHERE id = ?",
            (aliya_response, event_id),
        )
        self.db.commit()

    # ── Relationship ──

    def get_relationship_phase(self) -> int:
        """返回当前关系阶段。"""
        row = self.db.execute(
            "SELECT phase FROM relationship WHERE id = 1"
        ).fetchone()
        return row[0] if row else 1

    def get_relationship(self) -> dict | None:
        """返回完整的关系数据。"""
        row = self.db.execute(
            "SELECT phase, first_interaction_date, total_conversation_turns, "
            "active_days, last_active_date "
            "FROM relationship WHERE id = 1"
        ).fetchone()
        if not row:
            return None
        return {
            "phase": row[0],
            "first_interaction_date": row[1],
            "total_conversation_turns": row[2],
            "active_days": row[3],
            "last_active_date": row[4],
        }

    def init_relationship(self, date: str):
        """初始化关系记录（仅首次）。"""
        existing = self.db.execute(
            "SELECT id FROM relationship WHERE id = 1"
        ).fetchone()
        if not existing:
            self.db.execute(
                "INSERT INTO relationship (id, phase, first_interaction_date) "
                "VALUES (1, 1, ?)",
                (date,),
            )
            self.db.commit()

    def increment_turns(self):
        """对话轮次 +1。"""
        self.db.execute(
            "UPDATE relationship SET total_conversation_turns = total_conversation_turns + 1 "
            "WHERE id = 1"
        )
        self.db.commit()

    def log_active_day(self, date: str):
        """记录用户今天活跃（如果还没记录的话）。"""
        rel = self.get_relationship()
        if rel and rel["last_active_date"] == date:
            return  # 今天已经记录过了
        self.db.execute(
            "UPDATE relationship SET "
            "active_days = active_days + 1, "
            "last_active_date = ? "
            "WHERE id = 1",
            (date,),
        )
        self.db.commit()

    def update_phase(self, new_phase: int):
        """更新关系阶段。"""
        self.db.execute(
            "UPDATE relationship SET phase = ?, phase_updated_at = datetime('now') "
            "WHERE id = 1",
            (new_phase,),
        )
        self.db.commit()

    # ── Key-Value State ──

    def get_state(self, key: str, default: str = "") -> str:
        """获取一个状态值。"""
        row = self.db.execute(
            "SELECT value FROM aliya_state WHERE key = ?", (key,)
        ).fetchone()
        return row[0] if row else default

    def set_state(self, key: str, value: str):
        """设置一个状态值。"""
        self.db.execute(
            "INSERT OR REPLACE INTO aliya_state (key, value, updated_at) "
            "VALUES (?, ?, datetime('now'))",
            (key, value),
        )
        self.db.commit()

    # ── Last Message Time ──

    def get_last_message_time(self) -> str | None:
        """获取最近一条消息的时间。"""
        row = self.db.execute(
            "SELECT created_at FROM messages ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return row[0] if row else None

    # ── App Lifecycle ──

    def record_shutdown(self):
        """记录程序关闭时间。"""
        from datetime import datetime
        self.set_state("last_shutdown", datetime.now().isoformat())

    def get_last_shutdown(self) -> str | None:
        """获取上次程序关闭时间。"""
        val = self.get_state("last_shutdown", "")
        return val if val else None
