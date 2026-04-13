"""InfiniteClaw — War Room (Live Incident Dashboard)
When the SRE Watcher or a human detects a problem, this view becomes
the single pane of glass for incident response.
"""
import streamlit as st
import time
from ui.styles import inject_styles
from core.local_db import get_current_workspace_id, get_servers, get_server_tools, _get_connection
from core.ssh_manager import ssh_manager


def get_recent_incidents(ws_id: str, limit: int = 10):
    conn = _get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT * FROM activity_logs WHERE workspace_id = ? AND event_type = 'auto_heal' ORDER BY created_at DESC LIMIT ?",
        (ws_id, limit)
    )
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def render_war_room():
    inject_styles()
    st.markdown("<h2 style='color:#ef4444;'>War Room — Live Incident Dashboard</h2>", unsafe_allow_html=True)
    st.markdown("Your single pane of glass during an outage. Real-time server vitals, logs, and AI-assisted diagnosis.")

    ws_id = get_current_workspace_id()
    if not ws_id:
        st.warning("No active workspace.")
        return

    servers = get_servers(ws_id)
    if not servers:
        st.info("No servers connected.")
        return

    tab1, tab2 = st.tabs(["Live Diagnostics", "Incident History"])

    with tab1:
        server_names = {s["name"]: s["id"] for s in servers}
        selected = st.selectbox("Select Server Under Investigation", list(server_names.keys()))
        server_id = server_names[selected]

        if st.button("Pull Live Diagnostics", type="primary", use_container_width=True):
            diagnostics = {}
            diag_commands = {
                "System Load": "uptime",
                "Memory Usage": "free -m",
                "Disk Usage": "df -h",
                "Top Processes (CPU)": "ps aux --sort=-%cpu | head -10",
                "Top Processes (Memory)": "ps aux --sort=-%mem | head -10",
                "Recent System Errors": "dmesg --level=err,warn 2>/dev/null | tail -15 || journalctl -p err --no-pager -n 15 2>/dev/null",
                "Docker Status": "docker ps -a --format 'table {{.Names}}\\t{{.Status}}\\t{{.Ports}}' 2>/dev/null || echo 'Docker not available'",
                "Failed Systemd Services": "systemctl --failed 2>/dev/null || echo 'N/A'",
                "Network Connections": "ss -tulnp 2>/dev/null | head -20",
            }

            with st.status("Pulling live diagnostics...", expanded=True) as status:
                for label, cmd in diag_commands.items():
                    st.write(f"Checking: **{label}**")
                    try:
                        result = ssh_manager.execute_on_server(server_id, cmd, timeout=10)
                        diagnostics[label] = result.get("stdout", "No output")
                    except Exception as e:
                        diagnostics[label] = f"Error: {e}"
                status.update(label="Diagnostics Complete", state="complete", expanded=False)

            # Display
            st.markdown("---")

            # Quick health metrics
            col1, col2, col3 = st.columns(3)
            load = diagnostics.get("System Load", "N/A")
            col1.metric("System Load", load.split("load average:")[-1].strip()[:20] if "load average:" in load else "N/A")

            mem = diagnostics.get("Memory Usage", "")
            mem_lines = mem.strip().split("\n")
            if len(mem_lines) > 1:
                parts = mem_lines[1].split()
                if len(parts) >= 3:
                    col2.metric("Memory", f"{parts[2]}MB / {parts[1]}MB used")

            failed = diagnostics.get("Failed Systemd Services", "")
            fail_count = failed.count("failed") if failed else 0
            col3.metric("Failed Services", fail_count)

            st.markdown("---")

            for label, output in diagnostics.items():
                with st.expander(f"**{label}**", expanded=("Error" in label or "Failed" in label)):
                    st.code(output[:3000], language="bash")

            # AI Diagnosis
            st.markdown("---")
            st.markdown("### AI Diagnosis")
            if st.button("Ask AI to Analyze Diagnostics"):
                with st.spinner("AI is analyzing server health..."):
                    try:
                        from core.llm_engine import engine
                        diag_summary = "\n".join([f"=== {k} ===\n{v[:500]}" for k, v in diagnostics.items()])
                        prompt = (
                            f"You are an SRE expert. Analyze this server diagnostic output and identify any issues, "
                            f"potential crashes, or performance bottlenecks. Provide specific remediation commands.\n\n"
                            f"{diag_summary}"
                        )
                        analysis = engine.quick_ask(prompt)
                        st.markdown(analysis)
                    except Exception as e:
                        st.error(f"AI analysis failed: {e}")

    with tab2:
        st.markdown("### Recent Auto-Heal Events")
        incidents = get_recent_incidents(ws_id)
        if not incidents:
            st.info("No auto-heal incidents recorded yet. The SRE Watcher will log events here when it detects and fixes crashes.")
        else:
            for inc in incidents:
                with st.expander(f"🚑 [{inc['created_at']}] {inc.get('tool_name', 'Unknown')} — {inc['detail'][:80]}"):
                    st.markdown(f"**Tool**: `{inc.get('tool_name', 'N/A')}`")
                    st.markdown(f"**Server**: `{inc.get('server_id', 'N/A')}`")
                    st.markdown(f"**Detail**: {inc['detail']}")
                    if inc.get("raw_output"):
                        st.code(inc["raw_output"][:2000], language="bash")
