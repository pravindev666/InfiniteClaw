"""
InfiniteClaw — CI/CD Workflow Visualization
Glass-into-the-cyberworld pipeline view.
"""
import streamlit as st
from core.local_db import get_servers, get_all_detected_tools, get_current_workspace_id
from tools.tool_router import tool_router


def render_workflow_view():
    """CI/CD pipeline flow visualization."""
    ws_id = get_current_workspace_id()
    st.markdown("## 🔄 CI/CD Workflow Visualizer")
    st.caption("Push code → see where it flows through your pipeline")
    st.markdown("---")

    # Detect which CI/CD and deployment tools are available
    all_tools = get_all_detected_tools(ws_id) if ws_id else []
    active_tools = {t["tool_name"]: t for t in all_tools if t["status"] == "running"}

    # Build pipeline stages
    stages = []

    # Stage 1: Source
    stages.append({
        "name": "Source Code",
        "icon": "📝",
        "tool": "git",
        "status": "active",
        "detail": "Developer pushes code to repository"
    })

    # Stage 2: CI (Jenkins / GitLab / GitHub Actions)
    ci_tools = ["jenkins", "gitlab", "github_actions"]
    ci_active = [t for t in ci_tools if t in active_tools]
    if ci_active:
        tool_name = ci_active[0]
        adapter = tool_router.get_adapter(tool_name)
        stages.append({
            "name": "Build & Test",
            "icon": adapter.icon if adapter else "🔧",
            "tool": adapter.display_name if adapter else tool_name,
            "status": "running",
            "detail": f"CI pipeline via {adapter.display_name if adapter else tool_name}"
        })
    else:
        stages.append({"name": "Build & Test", "icon": "🔧", "tool": "No CI tool", "status": "missing", "detail": "No CI tool detected"})

    # Stage 3: Security Scan
    sec_tools = ["sonarqube", "trivy"]
    sec_active = [t for t in sec_tools if t in active_tools]
    if sec_active:
        stages.append({"name": "Security Scan", "icon": "🛡️", "tool": ", ".join([tool_router.get_adapter(t).display_name for t in sec_active]), "status": "running", "detail": "Code & image scanning"})
    else:
        stages.append({"name": "Security Scan", "icon": "🛡️", "tool": "Not configured", "status": "missing", "detail": "No scanner detected"})

    # Stage 4: Build Image
    if "docker" in active_tools or "podman" in active_tools:
        ct = "docker" if "docker" in active_tools else "podman"
        adapter = tool_router.get_adapter(ct)
        stages.append({"name": "Build Image", "icon": "🐳", "tool": adapter.display_name, "status": "running", "detail": "Container image build"})
    else:
        stages.append({"name": "Build Image", "icon": "🐳", "tool": "No container runtime", "status": "missing", "detail": ""})

    # Stage 5: Push to Registry
    if "harbor" in active_tools or "nexus" in active_tools:
        reg = "harbor" if "harbor" in active_tools else "nexus"
        adapter = tool_router.get_adapter(reg)
        stages.append({"name": "Push to Registry", "icon": "📦", "tool": adapter.display_name, "status": "running", "detail": "Image stored in registry"})
    else:
        stages.append({"name": "Push to Registry", "icon": "📦", "tool": "Docker Hub", "status": "active", "detail": "Default registry"})

    # Stage 6: Deploy
    if "kubernetes" in active_tools:
        stages.append({"name": "Deploy", "icon": "☸️", "tool": "Kubernetes", "status": "running", "detail": "Deployed to cluster"})
    else:
        stages.append({"name": "Deploy", "icon": "🚀", "tool": "SSH / Manual", "status": "active", "detail": "Direct deployment"})

    # Stage 7: Monitor
    mon_tools = ["prometheus", "grafana", "splunk", "elk", "nagios", "zabbix"]
    mon_active = [t for t in mon_tools if t in active_tools]
    if mon_active:
        names = [tool_router.get_adapter(t).display_name for t in mon_active[:3]]
        stages.append({"name": "Monitor", "icon": "📡", "tool": ", ".join(names), "status": "running", "detail": "Real-time monitoring"})
    else:
        stages.append({"name": "Monitor", "icon": "📡", "tool": "Not configured", "status": "missing", "detail": ""})

    # ─── Render Pipeline ───
    st.markdown("### Pipeline Flow")
    cols = st.columns(len(stages))
    for i, stage in enumerate(stages):
        with cols[i]:
            color = {"running": "#22c55e", "active": "#00f0ff", "missing": "#94a3b8"}.get(stage["status"], "#94a3b8")
            border = {"running": "rgba(34,197,94,0.3)", "active": "rgba(0,240,255,0.3)", "missing": "rgba(148,163,184,0.2)"}.get(stage["status"], "rgba(148,163,184,0.2)")
            st.markdown(f"""
            <div style="text-align:center;padding:16px 8px;background:rgba(15,23,42,0.6);
                        border:1px solid {border};border-radius:12px;min-height:160px;">
                <div style="font-size:2rem;">{stage['icon']}</div>
                <div style="font-size:0.8rem;font-weight:700;color:{color};margin:8px 0;">{stage['name']}</div>
                <div style="font-size:0.7rem;color:var(--text-secondary);">{stage['tool']}</div>
                <div style="font-size:0.65rem;color:var(--text-secondary);margin-top:4px;">{stage['detail']}</div>
            </div>
            """, unsafe_allow_html=True)

            # Arrow between stages
            if i < len(stages) - 1:
                st.markdown(f"<div style='text-align:center;color:{color};font-size:1.2rem;'>→</div>", unsafe_allow_html=True)
