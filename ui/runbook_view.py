"""InfiniteClaw — Runbook Automation Engine
Define repeatable playbooks as ordered command sequences. Execute them
on-demand or schedule them via the SRE Watcher. Replaces Ansible Tower
for simple workflows.
"""
import streamlit as st
import json
import uuid
from datetime import datetime
from ui.styles import inject_styles
from core.local_db import get_current_workspace_id, get_servers, _get_connection
from core.ssh_manager import ssh_manager


def ensure_runbook_table():
    conn = _get_connection()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS runbooks (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        name TEXT NOT NULL,
        description TEXT DEFAULT '',
        steps_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS runbook_executions (
        id TEXT PRIMARY KEY,
        runbook_id TEXT NOT NULL,
        server_id TEXT NOT NULL,
        server_name TEXT NOT NULL,
        results_json TEXT NOT NULL,
        status TEXT NOT NULL,
        executed_at TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()


def get_runbooks(ws_id: str):
    conn = _get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM runbooks WHERE workspace_id = ? ORDER BY created_at DESC", (ws_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_runbook(ws_id: str, name: str, description: str, steps: list):
    conn = _get_connection()
    rb_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO runbooks (id, workspace_id, name, description, steps_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (rb_id, ws_id, name, description, json.dumps(steps), datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    return rb_id


def delete_runbook(rb_id: str):
    conn = _get_connection()
    conn.execute("DELETE FROM runbook_executions WHERE runbook_id = ?", (rb_id,))
    conn.execute("DELETE FROM runbooks WHERE id = ?", (rb_id,))
    conn.commit()
    conn.close()


def save_execution(rb_id: str, server_id: str, server_name: str, results: list, status: str):
    conn = _get_connection()
    exec_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO runbook_executions (id, runbook_id, server_id, server_name, results_json, status, executed_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (exec_id, rb_id, server_id, server_name, json.dumps(results), status, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_executions(rb_id: str, limit: int = 10):
    conn = _get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM runbook_executions WHERE runbook_id = ? ORDER BY executed_at DESC LIMIT ?", (rb_id, limit))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def render_runbook_view():
    inject_styles()
    ensure_runbook_table()

    st.markdown("<h2 style='color:#00f0ff;'>Runbook Automation Engine</h2>", unsafe_allow_html=True)
    st.markdown("Define repeatable command playbooks. Execute them on any server with one click. Your personal Ansible Tower.")

    ws_id = get_current_workspace_id()
    if not ws_id:
        st.warning("No active workspace.")
        return

    servers = get_servers(ws_id)
    tab1, tab2 = st.tabs(["My Runbooks", "Create New Runbook"])

    with tab2:
        st.markdown("### Define a New Runbook")
        name = st.text_input("Runbook Name", placeholder="Weekly Maintenance")
        description = st.text_area("Description", placeholder="Cleanup, update, and health check")

        st.markdown("### Steps (one command per line)")
        steps_text = st.text_area(
            "Commands",
            placeholder="sudo apt update\nsudo apt upgrade -y\nsudo docker system prune -f\ndf -h /\nfree -m",
            height=200
        )

        if st.button("Save Runbook", type="primary"):
            if not name.strip() or not steps_text.strip():
                st.error("Name and at least one step are required.")
            else:
                steps = [s.strip() for s in steps_text.strip().split("\n") if s.strip()]
                save_runbook(ws_id, name, description, steps)
                st.success(f"Runbook '{name}' saved with {len(steps)} steps!")
                st.rerun()

    with tab1:
        runbooks = get_runbooks(ws_id)
        if not runbooks:
            st.info("No runbooks yet. Create one in the 'Create New Runbook' tab.")
            return

        for rb in runbooks:
            steps = json.loads(rb["steps_json"])
            with st.expander(f"**{rb['name']}** — {len(steps)} steps"):
                st.markdown(f"*{rb.get('description', '')}*")
                st.markdown("**Steps:**")
                for i, step in enumerate(steps, 1):
                    st.code(f"{i}. {step}", language="bash")

                # Execute
                if servers:
                    server_names = {s["name"]: s["id"] for s in servers}
                    target = st.selectbox("Target Server", list(server_names.keys()), key=f"rb_target_{rb['id']}")

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Execute Runbook", key=f"exec_{rb['id']}", type="primary", use_container_width=True):
                            server_id = server_names[target]
                            results = []
                            all_ok = True

                            with st.status(f"Executing '{rb['name']}' on {target}...", expanded=True) as status:
                                for i, step in enumerate(steps, 1):
                                    st.write(f"Step {i}/{len(steps)}: `{step}`")
                                    try:
                                        result = ssh_manager.execute_on_server(server_id, step, timeout=30)
                                        ok = result.get("exit_code", -1) == 0
                                        results.append({"step": step, "stdout": result.get("stdout", ""), "stderr": result.get("stderr", ""), "exit_code": result.get("exit_code", -1), "success": ok})
                                        if not ok:
                                            all_ok = False
                                            st.write(f"Step {i} failed (exit {result.get('exit_code')}). Continuing...")
                                    except Exception as e:
                                        results.append({"step": step, "stdout": "", "stderr": str(e), "exit_code": -1, "success": False})
                                        all_ok = False

                                final_status = "success" if all_ok else "partial_failure"
                                status.update(label=f"Runbook Complete ({final_status})", state="complete", expanded=False)

                            save_execution(rb["id"], server_id, target, results, final_status)

                            for r in results:
                                icon = "🟢" if r["success"] else "🔴"
                                with st.expander(f"{icon} `{r['step']}` (exit: {r['exit_code']})"):
                                    if r["stdout"]:
                                        st.code(r["stdout"][:2000], language="bash")
                                    if r["stderr"]:
                                        st.error(r["stderr"][:500])

                    with col2:
                        if st.button("Delete", key=f"del_{rb['id']}", use_container_width=True):
                            delete_runbook(rb["id"])
                            st.rerun()

                # Execution history
                execs = get_executions(rb["id"], 5)
                if execs:
                    st.markdown("**Recent Executions:**")
                    for ex in execs:
                        st.markdown(f"- `{ex['executed_at']}` on **{ex['server_name']}** — {ex['status']}")
