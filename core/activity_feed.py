"""
InfiniteClaw — Activity Feed
Real-time event logging and retrieval.
"""
from core.local_db import log_activity, get_activity_logs, get_current_workspace_id

EVENT_ICONS = {
    "tool_call": "🔧", "ssh_command": "🖥️", "llm_error": "❌",
    "scan_complete": "🔍", "server_added": "🌐", "server_removed": "🗑️",
    "bot_created": "🤖", "chat_message": "💬", "login": "🔑",
    "tool_detected": "✅", "tool_missing": "⚪", "warning": "⚠️",
}


def log_event(event_type: str, detail: str, tool_name: str = None,
              server_id: str = None, raw_output: str = None):
    ws_id = get_current_workspace_id()
    if ws_id:
        log_activity(ws_id, event_type, detail, tool_name, server_id, raw_output)


def get_recent_events(limit: int = 30) -> list:
    ws_id = get_current_workspace_id()
    if not ws_id:
        return []
    return get_activity_logs(ws_id, limit)


def get_icon(event_type: str) -> str:
    return EVENT_ICONS.get(event_type, "📌")
