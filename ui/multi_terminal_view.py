"""InfiniteClaw — Multi-Server Terminal
Execute a single command on ALL selected servers simultaneously.
Results displayed side-by-side. Like tmux for the cloud.
"""
import streamlit as st
from ui.styles import inject_styles
from core.local_db import get_current_workspace_id, get_servers
from core.ssh_manager import ssh_manager


def render_multi_terminal():
    inject_styles()
    st.markdown("<h2 style='color:#00f0ff;'>Multi-Server Terminal</h2>", unsafe_allow_html=True)
    st.markdown("Execute one command across ALL selected servers simultaneously. Results displayed side-by-side.")

    ws_id = get_current_workspace_id()
    if not ws_id:
        st.warning("No active workspace.")
        return

    servers = get_servers(ws_id)
    if not servers:
        st.info("No servers connected. Add servers in Remote Servers first.")
        return

    # Server selection
    server_options = {s["name"]: s["id"] for s in servers}
    selected_servers = st.multiselect(
        "Select Servers (or select all)",
        list(server_options.keys()),
        default=list(server_options.keys())
    )

    # Command input
    command = st.text_input("Command", placeholder="uptime && free -m && df -h /", key="multi_cmd")
    timeout = st.slider("Timeout (seconds)", 5, 60, 15)

    if st.button("Execute on All Selected Servers", type="primary", use_container_width=True):
        if not command.strip():
            st.error("Enter a command.")
            return
        if not selected_servers:
            st.error("Select at least one server.")
            return

        st.markdown("---")
        results = {}

        with st.spinner(f"Executing on {len(selected_servers)} server(s)..."):
            for name in selected_servers:
                sid = server_options[name]
                try:
                    result = ssh_manager.execute_on_server(sid, command, timeout=timeout)
                    results[name] = {
                        "stdout": result.get("stdout", ""),
                        "stderr": result.get("stderr", ""),
                        "exit_code": result.get("exit_code", -1),
                        "success": result.get("exit_code", -1) == 0
                    }
                except Exception as e:
                    results[name] = {
                        "stdout": "",
                        "stderr": str(e),
                        "exit_code": -1,
                        "success": False
                    }

        # Display results side-by-side
        st.markdown(f"### Results: `{command}`")

        # Summary
        success_count = sum(1 for r in results.values() if r["success"])
        fail_count = len(results) - success_count
        col1, col2, col3 = st.columns(3)
        col1.metric("Servers", len(results))
        col2.metric("Success", success_count)
        col3.metric("Failed", fail_count)

        st.markdown("---")

        # Show results in columns (up to 3 wide)
        cols_per_row = min(len(results), 3)
        server_items = list(results.items())

        for i in range(0, len(server_items), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                idx = i + j
                if idx >= len(server_items):
                    break
                name, result = server_items[idx]
                with col:
                    status_icon = "🟢" if result["success"] else "🔴"
                    st.markdown(f"#### {status_icon} {name}")
                    st.markdown(f"Exit code: `{result['exit_code']}`")
                    if result["stdout"]:
                        st.code(result["stdout"][:3000], language="bash")
                    if result["stderr"]:
                        st.error(result["stderr"][:1000])

    # Command history / presets
    st.markdown("---")
    st.markdown("### Quick Commands")
    preset_cols = st.columns(4)
    presets = [
        ("System Info", "uname -a"),
        ("Disk Usage", "df -h /"),
        ("Memory", "free -m"),
        ("Docker Status", "docker ps --format 'table {{.Names}}\\t{{.Status}}'"),
    ]
    for i, (label, cmd) in enumerate(presets):
        with preset_cols[i]:
            if st.button(label, use_container_width=True, key=f"preset_{i}"):
                st.session_state["multi_cmd"] = cmd
                st.rerun()
