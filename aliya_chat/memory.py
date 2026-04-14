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
    """

    SUMMARIZATION_PROMPT = """You are a conversation memory extractor for a character named Aliya — a young woman engineer on a stranded spaceship, speaking with someone from 1000 years in the past.

Given the conversation below, produce a concise structured summary with these sections:

1. **Relationship State** — How the user relates to Aliya, communication style, trust level
2. **Key Facts Learned** — Discrete facts about the user (name, preferences, life details) as bullet points
3. **Emotional Arc** — How the conversation's emotional tone has evolved
4. **Unresolved Threads** — Questions asked but not answered, promises made, topics to revisit
5. **Conversation Metadata** — Main topics discussed

Be concise. Each bullet should be one sentence max. Omit small talk that carries no information.

If a previous summary exists, merge it with the new content — resolve conflicts in favor of newer information.

Previous summary:
{previous_summary}

New messages to incorporate:
{new_messages}

Output the complete updated summary:"""

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
