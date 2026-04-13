"""InfiniteClaw — Ghost Mode (SSH Audit Trail)
Surfaces every command ever executed by InfiniteClaw (human, AI, or SRE Watcher)
as a chronological, filterable compliance audit trail.
"""
import streamlit as st
from ui.styles import inject_styles
from core.local_db import get_current_workspace_id, _get_connection


def get_activity_logs(ws_id: str, event_filter: str = None, limit: int = 200):
    conn = _get_connection()
    c = conn.cursor()
    if event_filter and event_filter != "All":
        c.execute(
            "SELECT * FROM activity_logs WHERE workspace_id = ? AND event_type = ? ORDER BY created_at DESC LIMIT ?",
            (ws_id, event_filter, limit)
        )
    else:
        c.execute(
            "SELECT * FROM activity_logs WHERE workspace_id = ? ORDER BY created_at DESC LIMIT ?",
            (ws_id, limit)
        )
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_event_types(ws_id: str):
    conn = _get_connection()
    c = conn.cursor()
    c.execute("SELECT DISTINCT event_type FROM activity_logs WHERE workspace_id = ? ORDER BY event_type", (ws_id,))
    rows = c.fetchall()
    conn.close()
    return [r["event_type"] for r in rows]


def render_ghost_mode():
    inject_styles()
    st.markdown("<h2 style='color:#00f0ff;'>Ghost Mode — SSH Audit Trail</h2>", unsafe_allow_html=True)
    st.markdown("Every command InfiniteClaw has ever executed on your infrastructure. Full transparency. Zero hiding.")

    ws_id = get_current_workspace_id()
    if not ws_id:
        st.warning("No active workspace. Log in first.")
        return

    # Filters
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        event_types = ["All"] + get_event_types(ws_id)
        selected_type = st.selectbox("Filter by Event Type", event_types)
    with col2:
        limit = st.number_input("Max Results", value=100, min_value=10, max_value=500, step=10)
    with col3:
        if st.button("Export as CSV", use_container_width=True):
            logs = get_activity_logs(ws_id, selected_type if selected_type != "All" else None, limit)
            if logs:
                import csv
                import io
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=["created_at", "event_type", "tool_name", "server_id", "detail", "raw_output"])
                writer.writeheader()
                for log in logs:
                    writer.writerow({k: log.get(k, "") for k in ["created_at", "event_type", "tool_name", "server_id", "detail", "raw_output"]})
                st.download_button("Download CSV", output.getvalue(), file_name="infiniteclaw_audit_trail.csv", mime="text/csv")

    st.markdown("---")

    logs = get_activity_logs(ws_id, selected_type if selected_type != "All" else None, limit)

    if not logs:
        st.info("No activity logs yet. Start using InfiniteClaw and commands will appear here automatically.")
        return

    # Stats
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Events", len(logs))
    tool_calls = len([l for l in logs if l.get("event_type") == "tool_call"])
    heals = len([l for l in logs if l.get("event_type") == "auto_heal"])
    errors = len([l for l in logs if l.get("event_type") == "llm_error"])
    col2.metric("Tool Calls", tool_calls)
    col3.metric("Auto-Heals", heals)
    col4.metric("Errors", errors)

    st.markdown("---")

    # Log Stream
    for log in logs:
        event = log.get("event_type", "unknown")
        icon_map = {"tool_call": "🔧", "auto_heal": "🚑", "llm_error": "❌", "scan": "🔍", "deploy": "🚀"}
        icon = icon_map.get(event, "📋")
        tool = log.get("tool_name") or ""
        detail = log.get("detail", "")[:200]
        ts = log.get("created_at", "")

        with st.expander(f"{icon} [{ts}] **{event}** {f'({tool})' if tool else ''} — {detail[:80]}...", expanded=False):
            st.markdown(f"**Event**: `{event}`")
            st.markdown(f"**Timestamp**: `{ts}`")
            if tool:
                st.markdown(f"**Tool**: `{tool}`")
            if log.get("server_id"):
                st.markdown(f"**Server ID**: `{log['server_id']}`")
            st.markdown(f"**Detail**: {detail}")
            if log.get("raw_output"):
                st.code(log["raw_output"][:3000], language="bash")
