"""
InfiniteClaw — Local SQLite Database
All persistent data lives here. No cloud dependencies.
"""
import sqlite3
import os
import json
import uuid
from typing import Dict, List, Optional
from datetime import datetime
from core.config import DB_PATH

_current_user_id = None
_current_workspace_id = None


def _get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def get_current_user_id() -> Optional[str]:
    return _current_user_id


def set_current_user_id(uid: str):
    global _current_user_id
    _current_user_id = uid


def get_current_workspace_id() -> Optional[str]:
    return _current_workspace_id


def set_current_workspace_id(ws_id: str):
    global _current_workspace_id
    _current_workspace_id = ws_id


def init_db():
    conn = _get_connection()
    try:
        conn.execute("PRAGMA journal_mode=WAL")
    except sqlite3.OperationalError:
        pass

    c = conn.cursor()

    # ─── Users ───
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        xp INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    try:
        c.execute("ALTER TABLE users ADD COLUMN xp INTEGER DEFAULT 0")
        c.execute("ALTER TABLE users ADD COLUMN level INTEGER DEFAULT 1")
    except sqlite3.OperationalError:
        pass

    # ─── Badges ───
    c.execute('''
    CREATE TABLE IF NOT EXISTS user_badges (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        badge_name TEXT NOT NULL,
        badge_icon TEXT NOT NULL,
        earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        UNIQUE(user_id, badge_name)
    )
    ''')

    # ─── Workspaces ───
    c.execute('''
    CREATE TABLE IF NOT EXISTS workspaces (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')

    # ─── Pipeline Snapshots (God-Mode) ───
    c.execute('''
    CREATE TABLE IF NOT EXISTS pipeline_snapshots (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        state_json TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
    )
    ''')

    # ─── SSH Servers ───
    c.execute('''
    CREATE TABLE IF NOT EXISTS servers (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        name TEXT NOT NULL,
        host TEXT NOT NULL,
        port INTEGER DEFAULT 22,
        username TEXT NOT NULL,
        auth_method TEXT DEFAULT 'password',
        password TEXT,
        key_content TEXT,
        key_path TEXT,
        last_scan TIMESTAMP,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
    )
    ''')

    # ─── Server Tool Detection ───
    c.execute('''
    CREATE TABLE IF NOT EXISTS server_tools (
        id TEXT PRIMARY KEY,
        server_id TEXT NOT NULL,
        tool_name TEXT NOT NULL,
        status TEXT DEFAULT 'unknown',
        version TEXT,
        port INTEGER,
        extra_info TEXT DEFAULT '{}',
        detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(server_id) REFERENCES servers(id) ON DELETE CASCADE,
        UNIQUE(server_id, tool_name)
    )
    ''')

    # ─── Bots ───
    c.execute('''
    CREATE TABLE IF NOT EXISTS bots (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        name TEXT NOT NULL,
        model TEXT NOT NULL,
        prompt TEXT NOT NULL,
        user_context TEXT DEFAULT '',
        memory TEXT DEFAULT '',
        fallback_models TEXT DEFAULT '[]',
        telegram_token TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
    )
    ''')

    # ─── API Keys Vault ───
    c.execute('''
    CREATE TABLE IF NOT EXISTS api_keys_vault (
        user_id TEXT PRIMARY KEY,
        openai_key TEXT,
        anthropic_key TEXT,
        nvidia_key TEXT,
        google_key TEXT,
        deepseek_key TEXT,
        dynamic_keys TEXT DEFAULT '{}',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')

    # ─── Chat History ───
    c.execute('''
    CREATE TABLE IF NOT EXISTS chat_history (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        bot_id TEXT,
        tool_context TEXT DEFAULT '',
        server_id TEXT,
        title TEXT DEFAULT 'New Chat',
        messages TEXT DEFAULT '[]',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
    )
    ''')

    # ─── Activity Logs ───
    c.execute('''
    CREATE TABLE IF NOT EXISTS activity_logs (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        event_type TEXT NOT NULL,
        tool_name TEXT,
        server_id TEXT,
        detail TEXT NOT NULL,
        raw_output TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # ─── Usage Analytics ───
    c.execute('''
    CREATE TABLE IF NOT EXISTS usage_logs (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        bot_id TEXT,
        model TEXT NOT NULL,
        prompt_tokens INTEGER DEFAULT 0,
        completion_tokens INTEGER DEFAULT 0,
        total_tokens INTEGER DEFAULT 0,
        estimated_cost REAL DEFAULT 0.0,
        response_time_ms INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # ─── Sessions ───
    c.execute('''
    CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')

    conn.commit()
    conn.close()


# ═══════════════════════ USER OPERATIONS ═══════════════════════

def create_user(email: str, password_hash: str) -> str:
    conn = _get_connection()
    user_id = str(uuid.uuid4())
    try:
        conn.execute(
            "INSERT INTO users (id, email, password_hash) VALUES (?, ?, ?)",
            (user_id, email, password_hash)
        )
        conn.commit()
        return user_id
    except sqlite3.IntegrityError:
        raise ValueError("Email already exists")
    finally:
        conn.close()


def get_user_by_email(email: str) -> Optional[Dict]:
    conn = _get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: str) -> Optional[Dict]:
    conn = _get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


# ═══════════════════════ GAMIFICATION ═══════════════════════

def award_xp(user_id: str, amount: int):
    conn = _get_connection()
    c = conn.cursor()
    c.execute("SELECT xp, level FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    if row:
        new_xp = row["xp"] + amount
        new_level = (new_xp // 1000) + 1
        c.execute("UPDATE users SET xp = ?, level = ? WHERE id = ?", (new_xp, new_level, user_id))
    conn.commit()
    conn.close()


def award_badge(user_id: str, badge_name: str, badge_icon: str) -> bool:
    """Returns True if badge is newly awarded, False if already had it."""
    conn = _get_connection()
    try:
        conn.execute("INSERT INTO user_badges (id, user_id, badge_name, badge_icon) VALUES (?, ?, ?, ?)",
                     (str(uuid.uuid4()), user_id, badge_name, badge_icon))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_user_gamification(user_id: str) -> Dict:
    conn = _get_connection()
    c = conn.cursor()
    c.execute("SELECT xp, level FROM users WHERE id = ?", (user_id,))
    user_row = c.fetchone()
    c.execute("SELECT badge_name, badge_icon FROM user_badges WHERE user_id = ? ORDER BY earned_at DESC", (user_id,))
    badges = [dict(r) for r in c.fetchall()]
    conn.close()
    if user_row:
        ur_dict = dict(user_row)
        return {"xp": ur_dict.get("xp", 0), "level": ur_dict.get("level", 1), "badges": badges}
    return {"xp": 0, "level": 1, "badges": []}


# ═══════════════════════ WORKSPACE OPERATIONS ═══════════════════════

def create_workspace(user_id: str, name: str) -> str:
    conn = _get_connection()
    ws_id = str(uuid.uuid4())
    conn.execute("INSERT INTO workspaces (id, user_id, name) VALUES (?, ?, ?)", (ws_id, user_id, name))
    conn.commit()
    conn.close()
    return ws_id


def get_or_create_workspace(user_id: str) -> str:
    conn = _get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM workspaces WHERE user_id = ? LIMIT 1", (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return row['id']
    return create_workspace(user_id, "Default Workspace")


# ═══════════════════════ SERVER OPERATIONS ═══════════════════════

def add_server(ws_id: str, name: str, host: str, port: int, username: str,
               auth_method: str = "password", password: str = None,
               key_content: str = None, key_path: str = None) -> str:
    conn = _get_connection()
    server_id = str(uuid.uuid4())
    conn.execute(
        """INSERT INTO servers (id, workspace_id, name, host, port, username,
           auth_method, password, key_content, key_path) VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (server_id, ws_id, name, host, port, username, auth_method, password, key_content, key_path)
    )
    conn.commit()
    conn.close()
    return server_id


def get_servers(ws_id: str) -> List[Dict]:
    conn = _get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM servers WHERE workspace_id = ? AND is_active = 1 ORDER BY name", (ws_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_server(server_id: str) -> Optional[Dict]:
    conn = _get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM servers WHERE id = ?", (server_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def delete_server(server_id: str):
    conn = _get_connection()
    conn.execute("DELETE FROM server_tools WHERE server_id = ?", (server_id,))
    conn.execute("DELETE FROM servers WHERE id = ?", (server_id,))
    conn.commit()
    conn.close()


def update_server_last_scan(server_id: str):
    conn = _get_connection()
    conn.execute("UPDATE servers SET last_scan = CURRENT_TIMESTAMP WHERE id = ?", (server_id,))
    conn.commit()
    conn.close()


# ═══════════════════════ SERVER TOOL DETECTION ═══════════════════════

def upsert_server_tool(server_id: str, tool_name: str, status: str,
                       version: str = None, port: int = None, extra_info: dict = None):
    conn = _get_connection()
    tool_id = str(uuid.uuid4())
    extra = json.dumps(extra_info or {})
    conn.execute(
        """INSERT INTO server_tools (id, server_id, tool_name, status, version, port, extra_info)
           VALUES (?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(server_id, tool_name) DO UPDATE SET
           status=excluded.status, version=excluded.version, port=excluded.port,
           extra_info=excluded.extra_info, detected_at=CURRENT_TIMESTAMP""",
        (tool_id, server_id, tool_name, status, version, port, extra)
    )
    conn.commit()
    conn.close()


def get_server_tools(server_id: str) -> List[Dict]:
    conn = _get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM server_tools WHERE server_id = ? ORDER BY tool_name", (server_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_detected_tools(ws_id: str) -> List[Dict]:
    conn = _get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT st.*, s.name as server_name, s.host as server_host
        FROM server_tools st
        JOIN servers s ON st.server_id = s.id
        WHERE s.workspace_id = ? AND s.is_active = 1
        ORDER BY st.tool_name, s.name
    """, (ws_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ═══════════════════════ BOT OPERATIONS ═══════════════════════

def create_bot(ws_id: str, name: str, model: str, prompt: str,
               fallback_models: List[str] = None, bot_id: str = None) -> str:
    if fallback_models is None:
        fallback_models = []
    conn = _get_connection()
    if not bot_id:
        bot_id = str(uuid.uuid4())
    conn.execute(
        """INSERT INTO bots (id, workspace_id, name, model, prompt, user_context, memory, fallback_models)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (bot_id, ws_id, name, model, prompt, "", "", json.dumps(fallback_models))
    )
    conn.commit()
    conn.close()
    return bot_id


def get_bots(ws_id: str) -> Dict[str, Dict]:
    conn = _get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM bots WHERE workspace_id = ?", (ws_id,))
    rows = c.fetchall()
    conn.close()
    bots = {}
    for r in rows:
        b = dict(r)
        bots[b['id']] = {
            "id": b['id'], "name": b['name'], "model": b['model'],
            "prompt": b['prompt'], "user_context": b.get('user_context', ''),
            "memory": b.get('memory', ''),
            "fallback_models": json.loads(b['fallback_models']) if b['fallback_models'] else [],
            "telegram_token": b.get('telegram_token')
        }
    return bots


def update_bot_memory(bot_id: str, new_memory: str):
    conn = _get_connection()
    conn.execute("UPDATE bots SET memory = ? WHERE id = ?", (new_memory, bot_id))
    conn.commit()
    conn.close()


def delete_bot(bot_id: str):
    conn = _get_connection()
    conn.execute("DELETE FROM chat_history WHERE bot_id = ?", (bot_id,))
    conn.execute("DELETE FROM bots WHERE id = ?", (bot_id,))
    conn.commit()
    conn.close()


# ═══════════════════════ API KEYS VAULT ═══════════════════════

def set_key_local(user_id: str, col_name: str, key: str):
    conn = _get_connection()
    c = conn.cursor()
    c.execute("SELECT user_id, dynamic_keys FROM api_keys_vault WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    standard_cols = ["openai_key", "anthropic_key", "nvidia_key", "google_key", "deepseek_key"]

    if row:
        if col_name in standard_cols:
            c.execute(f"UPDATE api_keys_vault SET {col_name} = ? WHERE user_id = ?", (key, user_id))
        else:
            dyn = json.loads(row["dynamic_keys"] or "{}")
            if key:
                dyn[col_name] = key
            elif col_name in dyn:
                del dyn[col_name]
            c.execute("UPDATE api_keys_vault SET dynamic_keys = ? WHERE user_id = ?", (json.dumps(dyn), user_id))
    else:
        if col_name in standard_cols:
            c.execute(f"INSERT INTO api_keys_vault (user_id, {col_name}) VALUES (?, ?)", (user_id, key))
        else:
            dyn = {col_name: key} if key else {}
            c.execute("INSERT INTO api_keys_vault (user_id, dynamic_keys) VALUES (?, ?)", (user_id, json.dumps(dyn)))
    conn.commit()
    conn.close()


def get_key_local(user_id: str, col_name: str) -> str:
    conn = _get_connection()
    c = conn.cursor()
    standard_cols = ["openai_key", "anthropic_key", "nvidia_key", "google_key", "deepseek_key"]
    if col_name in standard_cols:
        c.execute(f"SELECT {col_name} FROM api_keys_vault WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        return row[col_name] if row and row[col_name] else ""
    else:
        c.execute("SELECT dynamic_keys FROM api_keys_vault WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        if row and row["dynamic_keys"]:
            try:
                return json.loads(row["dynamic_keys"]).get(col_name, "")
            except Exception:
                pass
    return ""


# ═══════════════════════ CHAT HISTORY ═══════════════════════

def save_chat_history(ws_id: str, bot_id: str, title: str, messages: str,
                      chat_id: str = None, tool_context: str = "", server_id: str = None) -> str:
    conn = _get_connection()
    if chat_id:
        conn.execute(
            """UPDATE chat_history SET title=?, messages=?, updated_at=CURRENT_TIMESTAMP
               WHERE id=? AND workspace_id=?""",
            (title, messages, chat_id, ws_id)
        )
    else:
        chat_id = str(uuid.uuid4())
        conn.execute(
            """INSERT INTO chat_history (id, workspace_id, bot_id, tool_context, server_id, title, messages)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (chat_id, ws_id, bot_id, tool_context, server_id, title, messages)
        )
    conn.commit()
    conn.close()
    return chat_id


def get_chat_histories(ws_id: str) -> List[Dict]:
    conn = _get_connection()
    c = conn.cursor()
    c.execute("""SELECT id, bot_id, tool_context, server_id, title, created_at, updated_at
                 FROM chat_history WHERE workspace_id = ? ORDER BY updated_at DESC""", (ws_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_chat_history(chat_id: str) -> Optional[Dict]:
    conn = _get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM chat_history WHERE id = ?", (chat_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


# ═══════════════════════ ACTIVITY LOGS ═══════════════════════

def log_activity(ws_id: str, event_type: str, detail: str,
                 tool_name: str = None, server_id: str = None, raw_output: str = None):
    conn = _get_connection()
    conn.execute(
        """INSERT INTO activity_logs (id, workspace_id, event_type, tool_name, server_id, detail, raw_output)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (str(uuid.uuid4()), ws_id, event_type, tool_name, server_id, detail, raw_output)
    )
    conn.commit()
    conn.close()


def get_activity_logs(ws_id: str, limit: int = 50) -> List[Dict]:
    conn = _get_connection()
    c = conn.cursor()
    c.execute("""SELECT * FROM activity_logs WHERE workspace_id = ?
                 ORDER BY created_at DESC LIMIT ?""", (ws_id, limit))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ═══════════════════════ USAGE ANALYTICS ═══════════════════════

def log_usage(ws_id: str, bot_id: str, model: str, prompt_tokens: int,
              completion_tokens: int, total_tokens: int, estimated_cost: float,
              response_time_ms: int):
    conn = _get_connection()
    conn.execute(
        """INSERT INTO usage_logs (id, workspace_id, bot_id, model, prompt_tokens,
           completion_tokens, total_tokens, estimated_cost, response_time_ms)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (str(uuid.uuid4()), ws_id, bot_id, model, prompt_tokens,
         completion_tokens, total_tokens, estimated_cost, response_time_ms)
    )
    conn.commit()
    conn.close()


def get_usage_summary(ws_id: str) -> Dict:
    conn = _get_connection()
    c = conn.cursor()
    c.execute("""SELECT COUNT(*) as total_calls,
                 COALESCE(SUM(total_tokens),0) as total_tokens,
                 COALESCE(SUM(estimated_cost),0.0) as total_cost,
                 COALESCE(AVG(response_time_ms),0) as avg_response_ms
                 FROM usage_logs WHERE workspace_id = ?""", (ws_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else {}

# ═══════════════════════ PIPELINE TIME TRAVEL ═══════════════════════

def save_snapshot(ws_id: str, state_json: str):
    """Saves a snapshot of the pipeline graph for ⏪ Time Travel Rollbacks."""
    conn = _get_connection()
    # Keep only the last 20 snapshots per workspace to avoid DB bloat
    c = conn.cursor()
    c.execute("SELECT count(*) FROM pipeline_snapshots WHERE workspace_id = ?", (ws_id,))
    count = c.fetchone()[0]
    if count >= 20:
        c.execute("""DELETE FROM pipeline_snapshots WHERE id IN (
                     SELECT id FROM pipeline_snapshots WHERE workspace_id = ? 
                     ORDER BY created_at ASC LIMIT 1)""", (ws_id,))
    
    conn.execute(
        "INSERT INTO pipeline_snapshots (id, workspace_id, state_json) VALUES (?,?,?)",
        (str(uuid.uuid4()), ws_id, state_json)
    )
    conn.commit()
    conn.close()

def pop_latest_snapshot(ws_id: str) -> Optional[str]:
    """Retrieves and deletes the absolute latest snapshot (Undo mechanism)."""
    conn = _get_connection()
    c = conn.cursor()
    c.execute("SELECT id, state_json FROM pipeline_snapshots WHERE workspace_id = ? ORDER BY created_at DESC LIMIT 1", (ws_id,))
    row = c.fetchone()
    if row:
        conn.execute("DELETE FROM pipeline_snapshots WHERE id = ?", (row["id"],))
        conn.commit()
        conn.close()
        return row["state_json"]
    conn.close()
    return None
