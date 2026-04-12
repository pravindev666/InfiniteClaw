"""
InfiniteClaw — General Chat View
General-purpose AI chat, not tied to any specific tool.
"""
import streamlit as st
import json
from core.llm_engine import engine
from core.local_db import (
    save_chat_history, get_chat_histories, get_chat_history,
    get_current_workspace_id, get_servers
)
from core.ssh_manager import ssh_manager
from core.config import AVAILABLE_MODELS, DEFAULT_MODEL
from tools.tool_router import tool_router


def render_chat_view():
    """General AI chat interface."""
    ws_id = get_current_workspace_id()
    st.markdown("## 💬 AI Chat")
    st.caption("Ask me anything about DevOps, or command your infrastructure")
    st.markdown("---")

    # ─── Model Selector ───
    col1, col2 = st.columns([3, 1])
    with col1:
        _model = st.selectbox("🧠 Model", AVAILABLE_MODELS,
                              index=AVAILABLE_MODELS.index(DEFAULT_MODEL) if DEFAULT_MODEL in AVAILABLE_MODELS else 0)
        st.session_state["active_model"] = _model
    with col2:
        servers = get_servers(ws_id) if ws_id else []
        server_options = [("None", None)] + [(f"{s['name']} ({s['host']})", s["id"]) for s in servers]
        selected_server = st.selectbox(
            "🌐 Target Server",
            range(len(server_options)),
            format_func=lambda i: server_options[i][0]
        )
        active_server_id = server_options[selected_server][1]

    st.markdown("---")

    # ─── Chat History ───
    if "general_chat" not in st.session_state:
        st.session_state["general_chat"] = []

    messages = st.session_state["general_chat"]

    # Display
    for msg in messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-msg-user">👤 {msg["content"]}</div>', unsafe_allow_html=True)
        elif msg["role"] == "assistant":
            st.markdown(f'<div class="chat-msg-ai">∞ {msg["content"]}</div>', unsafe_allow_html=True)

    # Input
    user_input = st.chat_input("Talk to InfiniteClaw...")
    if user_input:
        messages.append({"role": "user", "content": user_input})

        # Build tool schemas
        tool_schemas = tool_router.get_tool_schemas() if active_server_id else tool_router._base_tool_schemas()

        def tool_executor(fn_name, fn_args):
            if not active_server_id:
                return "No server selected. Please select a target server."
            try:
                ssh_conn = ssh_manager.get_connection(active_server_id)
                return tool_router.execute_tool_call(ssh_conn, fn_name, fn_args)
            except Exception as e:
                return f"Error: {e}"

        with st.spinner("∞ Thinking..."):
            response = engine.chat(
                messages=messages,
                model=_model,
                tools=tool_schemas if active_server_id else None,
                tool_executor=tool_executor if active_server_id else None,
                tool_context="General DevOps",
                server_id=active_server_id,
            )

        messages.append({"role": "assistant", "content": response})

        # Save
        if ws_id:
            title = user_input[:50] + "..." if len(user_input) > 50 else user_input
            save_chat_history(ws_id, None, title, json.dumps(messages))

        st.rerun()

    # Clear button
    if messages:
        if st.button("🗑️ Clear Chat"):
            st.session_state["general_chat"] = []
            st.rerun()
