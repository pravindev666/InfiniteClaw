"""
InfiniteClaw — Dashboard View
Global infrastructure overview with server grid, tool matrix, and activity feed.
"""
import streamlit as st
import json
from ui.styles import metric_card, status_badge
from core.local_db import (
    get_servers, get_all_detected_tools, get_activity_logs,
    get_usage_summary, get_current_workspace_id
)
from tools.tool_router import TOOL_CATEGORIES, tool_router


def render_dashboard():
    """Main dashboard view — infrastructure at a glance."""
    ws_id = get_current_workspace_id()

    st.markdown("## 📊 Infrastructure Dashboard")
    st.markdown("---")

    servers = get_servers(ws_id) if ws_id else []
    all_tools = get_all_detected_tools(ws_id) if ws_id else []
    usage = get_usage_summary(ws_id) if ws_id else {}

    # ─── Top Metrics ───
    col1, col2, col3, col4 = st.columns(4)
    metric_card("Servers", str(len(servers)), col1)

    installed_count = len([t for t in all_tools if t["status"] in ("running", "stopped")])
    metric_card("Tools Detected", str(installed_count), col2)

    running_count = len([t for t in all_tools if t["status"] == "running"])
    metric_card("Tools Running", str(running_count), col3)

    total_tokens = usage.get("total_tokens", 0)
    metric_card("AI Tokens Used", f"{total_tokens:,}", col4)

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── Server Grid ───
    st.markdown("### 🌐 Connected Servers")
    if not servers:
        st.info("No servers connected yet. Go to **Remote Servers** to add one.")
    else:
        cols = st.columns(min(len(servers), 3))
        for i, srv in enumerate(servers):
            with cols[i % 3]:
                srv_tools = [t for t in all_tools if t.get("server_id") == srv["id"]]
                running = len([t for t in srv_tools if t["status"] == "running"])
                total = len([t for t in srv_tools if t["status"] in ("running", "stopped")])
                st.markdown(f"""
                <div class="glass-card">
                    <div style="font-weight:700;font-size:1.1rem;">🖥️ {srv['name']}</div>
                    <div style="color:var(--text-secondary);font-size:0.8rem;font-family:'JetBrains Mono',monospace;">
                        {srv['host']}:{srv.get('port', 22)}
                    </div>
                    <div style="margin-top:8px;">
                        {status_badge('running' if running > 0 else 'stopped')}
                        <span style="color:var(--text-secondary);margin-left:8px;">{running}/{total} tools active</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── Tool Detection Matrix ───
    st.markdown("### 🔍 Tool Detection Matrix")
    if all_tools:
        # Group by category
        for cat_key, cat_info in TOOL_CATEGORIES.items():
            cat_tools = [t for t in all_tools if t.get("tool_name") in cat_info["tools"]]
            if cat_tools:
                with st.expander(f"{cat_info['label']} ({len(cat_tools)} detected)", expanded=False):
                    for t in cat_tools:
                        adapter = tool_router.get_adapter(t["tool_name"])
                        icon = adapter.icon if adapter else "🔧"
                        name = adapter.display_name if adapter else t["tool_name"]
                        version = t.get("version", "")
                        version_str = f" v{version}" if version else ""
                        server_name = t.get("server_name", "")
                        st.markdown(
                            f"{status_badge(t['status'])} &nbsp; {icon} **{name}**{version_str} "
                            f"<span style='color:var(--text-secondary);'>on {server_name}</span>",
                            unsafe_allow_html=True
                        )
    else:
        st.info("No tools detected yet. Add a server and run a scan.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── Activity Feed ───
    st.markdown("### 📋 Recent Activity")
    if ws_id:
        logs = get_activity_logs(ws_id, limit=15)
        if logs:
            for log in logs:
                from core.activity_feed import get_icon
                icon = get_icon(log.get("event_type", ""))
                st.markdown(
                    f"<div style='padding:4px 0;border-bottom:1px solid var(--border-glass);font-size:0.8rem;'>"
                    f"{icon} <span style='color:var(--text-secondary);'>{log.get('created_at','')[:19]}</span> "
                    f"— {log.get('detail','')[:120]}</div>",
                    unsafe_allow_html=True
                )
        else:
            st.caption("No activity yet.")
