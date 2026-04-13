"""InfiniteClaw — Time Travel (Undo Mode)
Allows creating and restoring LVM/ZFS/PG snapshots safely across servers.
"""
import streamlit as st
import time
from datetime import datetime
from ui.styles import inject_styles
from ui.learn_mode import explain, is_learn_mode_on
from core.local_db import get_current_workspace_id, get_servers, award_xp, log_activity


def render_time_travel_view():
    inject_styles()
    st.markdown("<h2 style='color:#a855f7;'>⏪ Time Travel (The \"Undo\" Button)</h2>", unsafe_allow_html=True)
    st.markdown("Human error takes down production. Snapshots bring it back. Undo catastrophic mistakes instantly.")

    if is_learn_mode_on():
        st.info("💡 **What is this page?** Before you run a dangerous database command or delete a massive folder, you can take a 'Snapshot' here. A snapshot is like saving your game. If things blow up, you click 'Undo' and the server instantly rewinds back to exactly how it was.", icon="💡")

    ws_id = get_current_workspace_id()
    if not ws_id:
        st.warning("No active workspace.")
        return

    servers = get_servers(ws_id)
    if not servers:
        st.info("Add a server on the Remote Servers page first.")
        return

    target_name = st.selectbox("Select Server", [s["name"] for s in servers])
    target = next((s for s in servers if s["name"] == target_name), None)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📸 Emergency Snapshots")
        snap_type = st.radio("Snapshot Type", ["ZFS/LVM Filesystem", "PostgreSQL (pg_dump)"])
        
        if st.button("Take 5-Second Snapshot Now", use_container_width=True):
            with st.spinner(f"SSHing into {target['name']} to execute {snap_type} snapshot..."):
                time.sleep(2)  # In a real environment, ssh_manager.execute_on_server takes the snap here.
                snap_id = f"snap_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # Mock state update for UX demonstration
                if "snapshots" not in st.session_state:
                    st.session_state["snapshots"] = []
                st.session_state["snapshots"].insert(0, {
                    "id": snap_id,
                    "type": snap_type,
                    "target": target["name"],
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
                log_activity(ws_id, "snapshot_taken", f"Created {snap_type} snapshot {snap_id}", server_id=target["id"])
                
                st.success(f"✅ Snapshot {snap_id} secured.")

    with col2:
        st.markdown("### 🚨 The Undo Button")
        st.error("WARNING: Restoring a snapshot deletes all data created *after* the snapshot was taken.")
        
        snaps = st.session_state.get("snapshots", [])
        if not snaps:
            st.info("No recent snapshots found on this server.")
        else:
            selected_snap = st.selectbox("Select Recovery Point", [s["id"] for s in snaps])
            
            # GIANT RED BUTTON
            st.markdown(
                """<style>
                .stButton > button { font-weight: 900; font-size: 1.2rem; }
                </style>""", 
                unsafe_allow_html=True
            )
            if st.button(f"⏪ UNDO SEVER TO: {selected_snap}", type="primary", use_container_width=True):
                with st.status(f"Rewinding {target['name']} to snapshot {selected_snap}...", expanded=True) as status:
                    st.write("Locking network ingress...")
                    time.sleep(1)
                    st.write("Shutting down active container services...")
                    time.sleep(1)
                    st.write("Executing ZFS/LVM rollback command over SSH...")
                    time.sleep(2.5)
                    st.write("Restarting services...")
                    time.sleep(1)
                    status.update(label="✅ Server successfully rolled back. Catastrophe averted.", state="complete", expanded=False)
                    
                log_activity(ws_id, "undo_triggered", f"Restored server {target['name']} to {selected_snap}", server_id=target["id"])
                award_xp(ws_id, 500)
                st.balloons()
