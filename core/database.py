import sqlite3

DB_PATH = "db/lastfm_widget.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                discord_id TEXT PRIMARY KEY,
                lastfm_username TEXT NOT NULL,
                session_key TEXT NOT NULL,
                custom_avatar TEXT DEFAULT NULL,
                identity_id TEXT DEFAULT NULL
            )
        """)
        for col in ["custom_avatar TEXT DEFAULT NULL", "identity_id TEXT DEFAULT NULL"]:
            try:
                conn.execute(f"ALTER TABLE users ADD COLUMN {col}")
            except Exception:
                pass

def save_user(discord_id: str, lastfm_username: str, session_key: str = ""):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO users (discord_id, lastfm_username, session_key, identity_id)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(discord_id) DO UPDATE SET
                lastfm_username = excluded.lastfm_username,
                session_key = excluded.session_key,
                identity_id = COALESCE(identity_id, excluded.identity_id)
        """, (discord_id, lastfm_username, session_key, lastfm_username))

def get_user(discord_id: str) -> dict | None:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT lastfm_username, session_key, custom_avatar, identity_id FROM users WHERE discord_id = ?",
            (discord_id,)
        ).fetchone()
    if row:
        return {"lastfm_username": row[0], "session_key": row[1], "custom_avatar": row[2], "identity_id": row[3] or row[0]}
    return None

def set_custom_avatar(discord_id: str, url: str | None):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE users SET custom_avatar = ? WHERE discord_id = ?", (url, discord_id))

def is_identity_taken(identity_id: str, exclude_discord_id: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT 1 FROM users WHERE identity_id = ? AND discord_id != ?",
            (identity_id, exclude_discord_id)
        ).fetchone()
    return row is not None

def set_identity_id(discord_id: str, identity_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE users SET identity_id = ? WHERE discord_id = ?", (identity_id, discord_id))

def get_all_users() -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT discord_id, lastfm_username, custom_avatar, identity_id FROM users"
        ).fetchall()
    return [{"discord_id": r[0], "lastfm_username": r[1], "custom_avatar": r[2], "identity_id": r[3] or r[1]} for r in rows]

def delete_user(discord_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM users WHERE discord_id = ?", (discord_id,))
