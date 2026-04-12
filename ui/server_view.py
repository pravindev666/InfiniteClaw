"""
InfiniteClaw — Server Management View
Add, remove, test, and scan SSH servers.
"""
import streamlit as st
from core.local_db import (
    add_server, get_servers, delete_server, get_server_tools,
    get_current_workspace_id
)
from core.ssh_manager import ssh_manager
from tools.scanner import scan_server
from ui.styles import status_badge


def render_server_view():
    """Remote server management page."""
    ws_id = get_current_workspace_id()
    st.markdown("## 🌐 Remote Servers")
    st.caption("Manage SSH connections to your infrastructure")
    st.markdown("---")

    # ─── Add Server ───
    with st.expander("➕ Add New Server", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Server Name", placeholder="prod-web-01")
            host = st.text_input("Host / IP", placeholder="54.123.45.67")
            port = st.number_input("SSH Port", value=22, min_value=1, max_value=65535)
        with col2:
            username = st.text_input("Username", placeholder="ubuntu")
            auth_method = st.selectbox("Auth Method", ["password", "key"])
            if auth_method == "password":
                password = st.text_input("Password", type="password")
                key_content = None
            else:
                password = None
                key_file = st.file_uploader("Upload PEM Key", type=["pem", "key"])
                key_content = key_file.read().decode() if key_file else None

        if st.button("🔗 Connect & Add Server", use_container_width=True):
            if not all([name, host, username]):
                st.error("Name, host, and username are required.")
            elif not ws_id:
                st.error("No active workspace.")
            else:
                with st.spinner("Connecting..."):
                    server_id = add_server(
                        ws_id, name, host, port, username,
                        auth_method, password, key_content
                    )
                    # Test connection
                    test = ssh_manager.test_connection(server_id)
                    if test["success"]:
                        st.success(f"✅ Connected to {name}! Running tool scan...")
                        # Auto-scan
                        with st.spinner("🔍 Scanning for DevOps tools..."):
                            results = scan_server(server_id)
                        installed = [r for r in results if r["status"] not in ("not_installed", "error")]
                        st.success(f"Scan complete! Found **{len(installed)}** tools on {name}")
                        st.rerun()
                    else:
                        st.error(f"Connection failed: {test['message']}")
                        delete_server(server_id)

    st.markdown("---")

    # ─── Server List ───
    servers = get_servers(ws_id) if ws_id else []
    if not servers:
        st.info("No servers added yet. Use the form above to connect your first server.")
        return

    for srv in servers:
        with st.expander(f"🖥️ {srv['name']} — `{srv['host']}:{srv.get('port', 22)}`", expanded=True):
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                st.markdown(f"**User:** `{srv['username']}`")
                st.markdown(f"**Auth:** `{srv.get('auth_method', 'password')}`")
                last_scan = srv.get("last_scan", "Never")
                st.markdown(f"**Last Scan:** `{last_scan or 'Never'}`")

            with col2:
                if st.button("🔍 Re-Scan", key=f"scan_{srv['id']}"):
                    with st.spinner("Scanning..."):
                        results = scan_server(srv["id"])
                    installed = [r for r in results if r["status"] not in ("not_installed", "error")]
                    st.success(f"Found {len(installed)} tools")
                    st.rerun()

                if st.button("🔌 Test Connection", key=f"test_{srv['id']}"):
                    test = ssh_manager.test_connection(srv["id"])
                    if test["success"]:
                        st.success("✅ Connected")
                    else:
                        st.error(f"❌ {test['message']}")

            with col3:
                if st.button("🗑️ Remove", key=f"del_{srv['id']}", type="secondary"):
                    ssh_manager.close_connection(srv["id"])
                    delete_server(srv["id"])
                    st.rerun()

            # Show detected tools
            tools = get_server_tools(srv["id"])
            if tools:
                st.markdown("**Detected Tools:**")
                tool_cols = st.columns(4)
                for i, t in enumerate(tools):
                    if t["status"] in ("not_installed", "unknown"):
                        continue
                    adapter = None
                    try:
                        from tools.tool_router import tool_router
                        adapter = tool_router.get_adapter(t["tool_name"])
                    except Exception:
                        pass
                    icon = adapter.icon if adapter else "🔧"
                    dname = adapter.display_name if adapter else t["tool_name"]
                    version = f" v{t['version']}" if t.get("version") else ""
                    with tool_cols[i % 4]:
                        st.markdown(f"{icon} **{dname}**{version} {status_badge(t['status'])}", unsafe_allow_html=True)
