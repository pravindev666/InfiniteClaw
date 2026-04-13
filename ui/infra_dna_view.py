"""InfiniteClaw — Infrastructure DNA Fingerprinting
Captures a complete server fingerprint (OS, kernel, tools, ports, disk, CPU)
and stores snapshots for diffing over time to detect unauthorized changes.
"""
import streamlit as st
import json
import time
import uuid
from datetime import datetime
from ui.styles import inject_styles
from core.local_db import get_current_workspace_id, get_servers, _get_connection
from core.ssh_manager import ssh_manager


DNA_COMMANDS = {
    "hostname": "hostname 2>/dev/null",
    "os": "cat /etc/os-release 2>/dev/null | head -5",
    "kernel": "uname -r 2>/dev/null",
    "uptime": "uptime -p 2>/dev/null || uptime",
    "cpu_cores": "nproc 2>/dev/null",
    "memory_mb": "free -m 2>/dev/null | grep Mem | awk '{print $2}'",
    "disk_usage": "df -h / 2>/dev/null | tail -1",
    "open_ports": "ss -tlnp 2>/dev/null | grep LISTEN | awk '{print $4}' | sort",
    "users": "cut -d: -f1 /etc/passwd 2>/dev/null | sort | tail -20",
    "docker_version": "docker --version 2>/dev/null || echo 'Not installed'",
    "python_version": "python3 --version 2>/dev/null || echo 'Not installed'",
    "node_version": "node --version 2>/dev/null || echo 'Not installed'",
    "running_services": "systemctl list-units --type=service --state=running 2>/dev/null | head -20 || echo 'N/A'",
    "crontabs": "crontab -l 2>/dev/null || echo 'No crontabs'",
    "last_logins": "last -5 2>/dev/null || echo 'N/A'",
}


def save_dna_snapshot(ws_id: str, server_id: str, server_name: str, dna: dict):
    conn = _get_connection()
    snap_id = str(uuid.uuid4())
    conn.execute(
        """INSERT INTO infrastructure_dna (id, workspace_id, server_id, server_name, dna_json, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (snap_id, ws_id, server_id, server_name, json.dumps(dna), datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    return snap_id


def get_dna_snapshots(ws_id: str, server_id: str = None, limit: int = 20):
    conn = _get_connection()
    c = conn.cursor()
    if server_id:
        c.execute(
            "SELECT * FROM infrastructure_dna WHERE workspace_id = ? AND server_id = ? ORDER BY created_at DESC LIMIT ?",
            (ws_id, server_id, limit)
        )
    else:
        c.execute(
            "SELECT * FROM infrastructure_dna WHERE workspace_id = ? ORDER BY created_at DESC LIMIT ?",
            (ws_id, limit)
        )
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def ensure_dna_table():
    conn = _get_connection()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS infrastructure_dna (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        server_id TEXT NOT NULL,
        server_name TEXT NOT NULL,
        dna_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()


def render_infra_dna():
    inject_styles()
    ensure_dna_table()

    st.markdown("<h2 style='color:#00f0ff;'>Infrastructure DNA — Server Fingerprinting</h2>", unsafe_allow_html=True)
    st.markdown("Capture a complete genetic profile of any server. Compare snapshots over time to detect unauthorized changes.")

    ws_id = get_current_workspace_id()
    if not ws_id:
        st.warning("No active workspace.")
        return

    servers = get_servers(ws_id)
    if not servers:
        st.info("No servers connected. Add a server first.")
        return

    tab1, tab2 = st.tabs(["Capture DNA", "Compare Snapshots"])

    with tab1:
        server_names = {s["name"]: s["id"] for s in servers}
        selected = st.selectbox("Select Server", list(server_names.keys()), key="dna_server")

        if st.button("Capture DNA Snapshot", type="primary", use_container_width=True):
            server_id = server_names[selected]
            dna = {}

            with st.status("Extracting server genome...", expanded=True) as status:
                for key, cmd in DNA_COMMANDS.items():
                    st.write(f"Probing: **{key}**")
                    try:
                        result = ssh_manager.execute_on_server(server_id, cmd, timeout=10)
                        dna[key] = result.get("stdout", "").strip()
                    except Exception as e:
                        dna[key] = f"Error: {e}"
                status.update(label="DNA Extraction Complete", state="complete", expanded=False)

            save_dna_snapshot(ws_id, server_id, selected, dna)
            st.success(f"DNA snapshot saved for **{selected}**!")

            st.markdown("### Server Genome")
            for key, value in dna.items():
                with st.expander(f"**{key}**"):
                    st.code(value, language="bash")

    with tab2:
        server_names2 = {s["name"]: s["id"] for s in servers}
        selected2 = st.selectbox("Select Server", list(server_names2.keys()), key="dna_compare_server")
        snapshots = get_dna_snapshots(ws_id, server_names2[selected2])

        if len(snapshots) < 2:
            st.info("Need at least 2 snapshots to compare. Capture more DNA profiles over time.")
        else:
            snap_labels = [f"{s['created_at']}" for s in snapshots]
            col1, col2 = st.columns(2)
            with col1:
                idx_a = st.selectbox("Snapshot A (older)", range(len(snap_labels)), format_func=lambda i: snap_labels[i], key="snap_a")
            with col2:
                idx_b = st.selectbox("Snapshot B (newer)", range(len(snap_labels)), format_func=lambda i: snap_labels[i], index=min(1, len(snap_labels)-1), key="snap_b")

            if st.button("Diff Snapshots", use_container_width=True):
                dna_a = json.loads(snapshots[idx_a]["dna_json"])
                dna_b = json.loads(snapshots[idx_b]["dna_json"])

                changes = []
                all_keys = set(list(dna_a.keys()) + list(dna_b.keys()))
                for key in sorted(all_keys):
                    val_a = dna_a.get(key, "N/A")
                    val_b = dna_b.get(key, "N/A")
                    if val_a != val_b:
                        changes.append((key, val_a, val_b))

                if not changes:
                    st.success("No changes detected between snapshots. Server genome is stable.")
                else:
                    st.warning(f"**{len(changes)} mutation(s) detected!**")
                    for key, old, new in changes:
                        with st.expander(f"MUTATION: **{key}**", expanded=True):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown("**Before:**")
                                st.code(old, language="bash")
                            with col2:
                                st.markdown("**After:**")
                                st.code(new, language="bash")
