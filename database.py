import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_DB_PATH = Path(__file__).resolve().parent / "chat.db"
DB_PATH = Path(os.getenv("CHAT_DB_PATH") or DEFAULT_DB_PATH)


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    with closing(get_connection()) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")

        connection.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                visitor_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        columns = connection.execute("PRAGMA table_info(conversations)")
        if not any(column["name"] == "visitor_id" for column in columns):
            connection.execute("ALTER TABLE conversations ADD COLUMN visitor_id TEXT")
        connection.execute("""
            CREATE INDEX IF NOT EXISTS conversations_visitor_id
            ON conversations (visitor_id, id)
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL
                    CHECK (role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id)
                    REFERENCES conversations(id)
                    ON DELETE CASCADE
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS demo_usage (
                day TEXT NOT NULL,
                action TEXT NOT NULL,
                visitor_id TEXT NOT NULL,
                count INTEGER NOT NULL,
                PRIMARY KEY (day, action, visitor_id)
            )
        """)


def create_conversation(title: str, visitor_id: str | None = None):
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO conversations (title, visitor_id) VALUES (?, ?)",
            (title, visitor_id),
        )
        return cursor.lastrowid


def save_message(conversation_id: int, role: str, content: str):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO messages (conversation_id, role, content)
            VALUES (?, ?, ?)
            """,
            (conversation_id, role, content)
        )


def get_messages(conversation_id: int):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, role, content, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC
            """,
            (conversation_id,)
        ).fetchall()

        return [dict(row) for row in rows]

def conversation_exists(conversation_id: int, visitor_id: str | None = None) -> bool:
    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT 1 FROM conversations WHERE id = ? AND visitor_id IS ?",
            (conversation_id, visitor_id),
        ).fetchone()
        return row is not None
    finally:
        connection.close()

def get_conversations(visitor_id: str | None = None):
    connection = get_connection()

    try:
        rows = connection.execute("""
            SELECT id, title, created_at
            FROM conversations
            WHERE visitor_id IS ?
            ORDER BY id DESC
        """, (visitor_id,)).fetchall()

        return [dict(row) for row in rows]
    finally:
        connection.close()

def update_conversation_title(conversation_id: int, title: str):
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE conversations
            SET title = ?
            WHERE id = ?
            """,
            (title, conversation_id)
        )


def reserve_demo_slot(visitor_id: str, action: str, visitor_limit: int, site_limit: int) -> bool:
    day = datetime.now(timezone.utc).date().isoformat()
    with closing(get_connection()) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        rows = connection.execute(
            """SELECT visitor_id, count FROM demo_usage
               WHERE day = ? AND action = ? AND visitor_id IN (?, '')""",
            (day, action, visitor_id),
        )
        counts = {row["visitor_id"]: row["count"] for row in rows}
        if counts.get(visitor_id, 0) >= visitor_limit or counts.get("", 0) >= site_limit:
            return False

        connection.execute("DELETE FROM demo_usage WHERE day < ?", (day,))
        connection.executemany(
            """INSERT INTO demo_usage (day, action, visitor_id, count)
               VALUES (?, ?, ?, 1)
               ON CONFLICT (day, action, visitor_id) DO UPDATE SET count = count + 1""",
            [(day, action, visitor_id), (day, action, "")],
        )
        return True
