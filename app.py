"""
InfiniteClaw — Main Streamlit Entry Point
Launch with: streamlit run app.py
"""
import streamlit as st
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.local_db import init_db
from ui.views import render_login, render_main

# ─── Page Config ───
st.set_page_config(
    page_title="InfiniteClaw — DevOps AI Command Center",
    page_icon="∞",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "InfiniteClaw v1.0 — One Claw To Rule Them All. Infinite Reach. Total Control."
    }
)

# ─── Initialize Database ───
init_db()

# ─── Route ───
if "user_id" not in st.session_state or not st.session_state.get("user_id"):
    render_login()
else:
    # Restore session context
    from core.local_db import set_current_user_id, set_current_workspace_id, get_or_create_workspace
    user_id = st.session_state["user_id"]
    set_current_user_id(user_id)

    ws_id = st.session_state.get("workspace_id")
    if not ws_id:
        ws_id = get_or_create_workspace(user_id)
        st.session_state["workspace_id"] = ws_id
    set_current_workspace_id(ws_id)

    render_main()
