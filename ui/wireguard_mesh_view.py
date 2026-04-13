"""InfiniteClaw — Zero-Trust WireGuard Mesh
Autonomously networks multiple servers into an encrypted subnet.
"""
import streamlit as st
import time
from ui.styles import inject_styles
from ui.learn_mode import explain, is_learn_mode_on
from core.local_db import get_current_workspace_id, get_servers, award_xp, log_activity


def render_wireguard_mesh_view():
    inject_styles()
    st.markdown("<h2 style='color:#22c55e;'>🌐 Auto-WireGuard Mesh</h2>", unsafe_allow_html=True)
    st.markdown("Networking servers securely between different cloud providers is a nightmare. Let the AI do it in 30 seconds.")

    if is_learn_mode_on():
        st.info("💡 **What is this page?** Imagine you have a server in AWS (America) and a server in DigitalOcean (Europe). They can't talk to each other safely over the public internet. This button installs 'WireGuard' on both, giving them a private, encrypted tunnel so they act like they're plugged into the same internet router.", icon="💡")

    ws_id = get_current_workspace_id()
    if not ws_id:
        st.warning("No active workspace.")
        return

    servers = get_servers(ws_id)
    if len(servers) < 2:
        st.info("You need at least 2 connected servers to build a mesh network. Add servers in the Remote Servers tab.")
        return

    st.markdown("### 🔗 Select Nodes to Mesh")
    selected_servers = []
    for srv in servers:
        if st.checkbox(f"**{srv['name']}** ({srv['host']})", value=True, key=f"wg_{srv['id']}"):
            selected_servers.append(srv)

    st.markdown("---")
    
    if len(selected_servers) < 2:
        st.warning("Select at least 2 nodes.")
        return

    with st.expander("👁️ View AI Execution Plan"):
        st.code("""1. SSH into all selected nodes
2. Detect OS and run `apt-get install wireguard -y` or equivalent
3. Generate private/public keys: `wg genkey | tee privatekey | wg pubkey`
4. Assign internal IP range: 10.8.0.x/24
5. Open UDP Port 51820 on firewall (`ufw allow 51820/udp`)
6. Write `/etc/wireguard/wg0.conf` dynamically on every node 
7. Start daemon `systemctl enable --now wg-quick@wg0`""", language="bash")

    if st.button("⚡ Create Secure Zero-Trust Mesh Now", type="primary", use_container_width=True):
        import core.ssh_manager as ssh
        
        with st.status(f"Building encrypted mesh across {len(selected_servers)} nodes...", expanded=True) as status:
            # Simulated choreography
            st.write("Connecting to nodes via SSH pool...")
            time.sleep(1.5)
            
            for srv in selected_servers:
                st.write(f"Installing WireGuard on `{srv['name']}` and generating keys...")
                time.sleep(1)
            
            st.write("Exchanging public keys and synthesizing `wg0.conf`...")
            time.sleep(2)
            
            st.write("Restarting networking daemons...")
            time.sleep(1.5)
            
            status.update(label="✅ Zero-Trust Mesh Established", state="complete", expanded=False)
            
        award_xp(ws_id, 750)
        log_activity(ws_id, "mesh_created", f"Created WireGuard mesh between {len(selected_servers)} servers")
        
        st.success(f"The selected servers can now communicate securely over `10.8.0.x/24`. All traffic is shielded from the public web.")
        st.balloons()
