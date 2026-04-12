"""
InfiniteClaw — DevOps Tool View
Generic tool page with pictorial GUI + AI chatbox, used by all 30 tools.
"""
import streamlit as st
import json
from core.local_db import (
    get_servers, get_server_tools, get_current_workspace_id,
    save_chat_history, get_chat_history
)
from core.ssh_manager import ssh_manager
from core.llm_engine import engine
from tools.tool_router import tool_router
from ui.styles import status_badge, metric_card


def render_tool_page(tool_name: str):
    """Render a DevOps tool page with dashboard + AI chatbox."""
    adapter = tool_router.get_adapter(tool_name)
    if not adapter:
        st.error(f"Unknown tool: {tool_name}")
        return

    ws_id = get_current_workspace_id()
    servers = get_servers(ws_id) if ws_id else []

    # ─── Header ───
    st.markdown(f"## {adapter.icon} {adapter.display_name}")
    st.caption(adapter.description)
    st.markdown("---")

    # ─── Server Selector ───
    if not servers:
        st.warning("No servers connected. Go to **Remote Servers** to add one.")
        return

    # Find servers where this tool is detected
    tool_servers = []
    for srv in servers:
        srv_tools = get_server_tools(srv["id"])
        for t in srv_tools:
            if t["tool_name"] == tool_name and t["status"] != "not_installed":
                tool_servers.append((srv, t))
                break

    if not tool_servers:
        # Show all servers as options anyway
        st.info(f"{adapter.display_name} not detected on any server. Select a server to scan or install.")
        selected_server = st.selectbox(
            "🌐 Select Server",
            servers,
            format_func=lambda s: f"{s['name']} ({s['host']})"
        )
        if selected_server:
            _render_not_installed(adapter, selected_server)
        return

    # Server dropdown
    selected_idx = st.selectbox(
        "🌐 Select Server",
        range(len(tool_servers)),
        format_func=lambda i: f"{tool_servers[i][0]['name']} ({tool_servers[i][0]['host']}) — {tool_servers[i][1]['status'].upper()}"
    )

    server, tool_info = tool_servers[selected_idx]

    # ─── Status Bar ───
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"**Server:** `{server['host']}:{server.get('port', 22)}`", unsafe_allow_html=True)
    with col2:
        st.markdown(f"**Status:** {status_badge(tool_info['status'])}", unsafe_allow_html=True)
    with col3:
        version = tool_info.get("version", "N/A")
        port = tool_info.get("port", "—")
        st.markdown(f"**Version:** `{version}` &nbsp; **Port:** `{port}`")

    st.markdown("---")

    # ─── Pictorial GUI Panel ───
    st.markdown("### 📺 Live Dashboard")
    try:
        ssh_conn = ssh_manager.get_connection(server["id"])
        dashboard_data = adapter.get_dashboard_data(ssh_conn)

        # Render dashboard data in expandable sections
        for key, value in dashboard_data.items():
            if isinstance(value, str) and len(value) > 10:
                with st.expander(f"📊 {key.replace('_', ' ').title()}", expanded=True):
                    st.code(value, language="text")
            elif isinstance(value, dict):
                with st.expander(f"📊 {key.replace('_', ' ').title()}", expanded=False):
                    st.json(value)
            else:
                st.caption(f"**{key}:** {value}")
    except Exception as e:
        st.error(f"Cannot connect to server: {e}")

    st.markdown("---")

    # ─── AI Chatbox ───
    st.markdown("### 💬 AI Assistant")
    st.caption(f"Ask me anything about {adapter.display_name} on this server")

    # Chat state
    chat_key = f"chat_{tool_name}_{server['id']}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    messages = st.session_state[chat_key]

    # Display chat history
    chat_container = st.container()
    with chat_container:
        for msg in messages:
            role = msg["role"]
            if role == "user":
                st.markdown(f'<div class="chat-msg-user">👤 {msg["content"]}</div>', unsafe_allow_html=True)
            elif role == "assistant":
                st.markdown(f'<div class="chat-msg-ai">∞ {msg["content"]}</div>', unsafe_allow_html=True)

    # Chat input
    user_input = st.chat_input(f"Ask about {adapter.display_name}...")
    if user_input:
        messages.append({"role": "user", "content": user_input})

        # Get tool schemas for context
        tool_schemas = tool_router.get_tool_schemas(tool_name)

        # Create tool executor
        def tool_executor(fn_name, fn_args):
            try:
                ssh_conn = ssh_manager.get_connection(server["id"])
                return tool_router.execute_tool_call(ssh_conn, fn_name, fn_args)
            except Exception as e:
                return f"Error: {e}"

        # Call LLM engine
        with st.spinner("∞ Thinking..."):
            response = engine.chat(
                messages=messages,
                model=st.session_state.get("active_model", None),
                tools=tool_schemas,
                tool_executor=tool_executor,
                tool_context=adapter.display_name,
                server_id=server["id"],
            )

        messages.append({"role": "assistant", "content": response})
        st.session_state[chat_key] = messages

        # Save to DB
        if ws_id:
            save_chat_history(
                ws_id, None, f"{adapter.display_name} Chat",
                json.dumps(messages), tool_context=tool_name, server_id=server["id"]
            )

        st.rerun()


def _render_not_installed(adapter, server):
    """Render UI for when a tool is not installed on a server."""
    st.markdown(f"""
    <div class="glass-card" style="text-align:center;padding:40px;">
        <div style="font-size:3rem;">{adapter.icon}</div>
        <div style="font-size:1.2rem;font-weight:700;margin:10px 0;">{adapter.display_name}</div>
        <div style="color:var(--text-secondary);">
            {status_badge('not_installed')}<br><br>
            Not detected on <strong>{server['name']}</strong> ({server['host']})
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # AI chatbox still available for installation help
    st.markdown("### 💬 Need help installing?")
    user_input = st.chat_input(f"Ask me to install {adapter.display_name}...")
    if user_input:
        if f"chat_{adapter.name}_install" not in st.session_state:
            st.session_state[f"chat_{adapter.name}_install"] = []

        msgs = st.session_state[f"chat_{adapter.name}_install"]
        msgs.append({"role": "user", "content": user_input})

        tool_schemas = tool_router.get_tool_schemas()

        def tool_executor(fn_name, fn_args):
            try:
                ssh_conn = ssh_manager.get_connection(server["id"])
                return tool_router.execute_tool_call(ssh_conn, fn_name, fn_args)
            except Exception as e:
                return f"Error: {e}"

        with st.spinner("∞ Thinking..."):
            response = engine.chat(
                messages=msgs, tools=tool_schemas, tool_executor=tool_executor,
                tool_context=f"Installing {adapter.display_name}", server_id=server["id"]
            )

        msgs.append({"role": "assistant", "content": response})
        st.rerun()
