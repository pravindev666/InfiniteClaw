"""InfiniteClaw — Real FinOps Dashboard
Uses SSH to pull ACTUAL system metrics (docker stats, free -m, uptime)
from connected servers and identifies real idle/wasted resources.
"""
import streamlit as st
from ui.styles import inject_styles
from core.local_db import get_current_workspace_id, get_servers
from core.ssh_manager import ssh_manager


def render_finops_view():
    inject_styles()
    st.markdown("<h2 style='color:#00f0ff;'>CFO FinOps — Resource Waste Detector</h2>", unsafe_allow_html=True)
    st.markdown("Pull real CPU, memory, and container metrics from your servers to identify waste and idle resources.")

    ws_id = get_current_workspace_id()
    if not ws_id:
        st.warning("No active workspace.")
        return

    servers = get_servers(ws_id)
    if not servers:
        st.info("No servers connected. Add a server to begin real cost analysis.")
        return

    if st.button("Scan All Servers for Resource Waste", type="primary", use_container_width=True):
        all_data = {}

        with st.status("Pulling live metrics from all servers...", expanded=True) as status:
            for srv in servers:
                st.write(f"Scanning **{srv['name']}** ({srv['host']})...")
                data = {}
                try:
                    # System metrics
                    mem = ssh_manager.execute_on_server(srv["id"], "free -m 2>/dev/null", timeout=10)
                    data["memory"] = mem.get("stdout", "")

                    cpu = ssh_manager.execute_on_server(srv["id"], "top -bn1 | head -5 2>/dev/null || uptime", timeout=10)
                    data["cpu"] = cpu.get("stdout", "")

                    disk = ssh_manager.execute_on_server(srv["id"], "df -h / 2>/dev/null", timeout=10)
                    data["disk"] = disk.get("stdout", "")

                    # Docker stats (if available)
                    docker = ssh_manager.execute_on_server(
                        srv["id"],
                        "docker stats --no-stream --format 'table {{.Name}}\\t{{.CPUPerc}}\\t{{.MemUsage}}\\t{{.MemPerc}}' 2>/dev/null || echo 'Docker not available'",
                        timeout=15
                    )
                    data["docker"] = docker.get("stdout", "")

                    # Uptime
                    uptime = ssh_manager.execute_on_server(srv["id"], "uptime -p 2>/dev/null || uptime", timeout=5)
                    data["uptime"] = uptime.get("stdout", "").strip()

                    all_data[srv["name"]] = data
                except Exception as e:
                    all_data[srv["name"]] = {"error": str(e)}

            status.update(label="Scan Complete", state="complete", expanded=False)

        # Display
        st.markdown("---")

        for name, data in all_data.items():
            st.markdown(f"### {name}")

            if "error" in data:
                st.error(f"Connection failed: {data['error']}")
                continue

            col1, col2, col3 = st.columns(3)

            # Parse memory
            mem_lines = data.get("memory", "").strip().split("\n")
            if len(mem_lines) > 1:
                parts = mem_lines[1].split()
                if len(parts) >= 4:
                    total = int(parts[1])
                    used = int(parts[2])
                    free_mem = int(parts[3])
                    pct = (used / total * 100) if total > 0 else 0
                    with col1:
                        st.metric("Memory Used", f"{used}MB / {total}MB", delta=f"{pct:.0f}%")
                        if pct < 20:
                            st.warning("Under 20% memory usage — this server may be oversized.")

            # Parse disk
            disk_lines = data.get("disk", "").strip().split("\n")
            if len(disk_lines) > 1:
                parts = disk_lines[-1].split()
                if len(parts) >= 5:
                    with col2:
                        st.metric("Disk", f"{parts[2]} / {parts[1]} used", delta=parts[4])

            # Uptime
            with col3:
                st.metric("Uptime", data.get("uptime", "N/A")[:40])

            # Docker containers
            docker_out = data.get("docker", "")
            if docker_out and "Docker not available" not in docker_out:
                with st.expander("Docker Container Stats"):
                    st.code(docker_out[:2000], language="text")
                    # Check for idle containers
                    for line in docker_out.split("\n")[1:]:
                        if "0.00%" in line:
                            st.warning(f"Idle container detected: `{line.split()[0] if line.split() else 'unknown'}`")

            st.markdown("---")

        # AI Analysis
        if st.button("Ask AI for Cost Optimization Recommendations"):
            with st.spinner("AI is analyzing your infrastructure costs..."):
                try:
                    from core.llm_engine import engine
                    summary = "\n".join([
                        f"=== {name} ===\nMemory: {d.get('memory','N/A')[:300]}\nCPU: {d.get('cpu','N/A')[:300]}\nDocker: {d.get('docker','N/A')[:300]}"
                        for name, d in all_data.items() if "error" not in d
                    ])
                    prompt = (
                        "You are a FinOps expert. Analyze these server metrics and identify wasted resources, "
                        "oversized instances, and idle containers. Provide specific recommendations "
                        "with estimated monthly savings.\n\n" + summary
                    )
                    analysis = engine.quick_ask(prompt)
                    st.markdown(analysis)
                except Exception as e:
                    st.error(f"AI analysis failed: {e}")
