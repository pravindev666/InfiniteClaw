"""
InfiniteClaw — Main View Dispatcher
Sidebar navigation with collapsible categories for all 30 DevOps tools.
"""
import streamlit as st
import hashlib
from core.local_db import (
    init_db, get_user_by_email, create_user, get_or_create_workspace,
    set_current_user_id, set_current_workspace_id, get_current_workspace_id,
    get_all_detected_tools
)
from core.config import get_all_keys, set_key, AVAILABLE_MODELS
from ui.styles import inject_styles, sidebar_header
from ui.learn_mode import render_learn_mode_toggle, explain_sidebar
from ui.dashboard_view import render_dashboard
from ui.devops_tool_view import render_tool_page
from ui.server_view import render_server_view
from ui.chat_view import render_chat_view
from ui.workflow_view import render_workflow_view
from tools.tool_router import TOOL_CATEGORIES, tool_router


# ─── Navigation Map ───
CORE_PAGES = {
    "Infinity Core": "jarvis",
    "Code-to-Cloud": "deploy",
    "Terraform Drift": "drift",
    "Post-Mortems": "postmortem",
    "AI Red Team": "redteam",
    "DB Auto-Migrator": "migrator",
    "CFO FinOps": "finops",
    "SOC2 Auditor": "audit",
    "Ghost Mode": "ghost",
    "Secrets Scanner": "secrets",
    "Infra DNA": "dna",
    "Multi-Terminal": "multiterminal",
    "Runbooks": "runbooks",
    "War Room": "warroom",
    "Dashboard": "dashboard",
    "Flow Builder": "flow",
    "Chat": "chat",
    "Remote Servers": "servers",
    "CI/CD Workflow": "workflow",
    "Settings": "settings",
}

TOOL_NAV = {
    "ci_cd": {
        "label": "CI/CD",
        "items": [
            ("Jenkins", "jenkins"),
            ("GitLab CI", "gitlab"),
            ("ArgoCD", "argocd"),
            ("GitHub Actions", "github_actions"),
        ]
    },
    "containers": {
        "label": "Containers",
        "items": [
            ("Docker", "docker"),
            ("Kubernetes", "kubernetes"),
            ("Helm", "helm"),
            ("Podman", "podman"),
            ("Harbor", "harbor"),
        ]
    },
    "monitoring": {
        "label": "Monitoring",
        "items": [
            ("Prometheus", "prometheus"),
            ("Grafana", "grafana"),
            ("Splunk", "splunk"),
            ("ELK Stack", "elk"),
            ("Nagios", "nagios"),
            ("Jaeger", "jaeger"),
            ("Zabbix", "zabbix"),
        ]
    },
    "config_iac": {
        "label": "Config & IaC",
        "items": [
            ("Ansible", "ansible"),
            ("Terraform", "terraform"),
            ("Chef", "chef"),
            ("Puppet", "puppet"),
            ("Packer", "packer"),
            ("Vault", "vault"),
            ("Consul", "consul"),
        ]
    },
    "security": {
        "label": "Security",
        "items": [
            ("SonarQube", "sonarqube"),
            ("Trivy", "trivy"),
        ]
    },
    "networking": {
        "label": "Networking",
        "items": [
            ("Nginx", "nginx"),
            ("HAProxy", "haproxy"),
            ("Traefik", "traefik"),
        ]
    },
    "data": {
        "label": "Data & Messaging",
        "items": [
            ("Kafka", "kafka"),
            ("RabbitMQ", "rabbitmq"),
            ("Nexus", "nexus"),
        ]
    },
}


def _hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def render_login():
    """Login / Register screen."""
    inject_styles()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center;padding:40px 0;">
            <div style="font-size:4rem;">∞</div>
            <div style="font-size:2rem;font-weight:900;
                        background:linear-gradient(135deg,#00f0ff,#a855f7);
                        -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                ∞ INFINITECLAW
            </div>
            <div style="color:#94a3b8;font-size:0.8rem;letter-spacing:3px;margin-top:8px;">
                DEVOPS AI COMMAND CENTER
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.info("**First time here?** Click the 'Register' tab below to create a free account. Just pick any email and password — everything runs locally on your computer, nothing is sent to the cloud.", icon="👋")

        tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])

        with tab1:
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_pw")
            if st.button("Login", use_container_width=True, key="login_btn"):
                user = get_user_by_email(email)
                if user and user["password_hash"] == _hash_pw(password):
                    st.session_state["user_id"] = user["id"]
                    st.session_state["user_email"] = email
                    ws_id = get_or_create_workspace(user["id"])
                    set_current_user_id(user["id"])
                    set_current_workspace_id(ws_id)
                    st.rerun()
                else:
                    st.error("Invalid credentials")

        with tab2:
            reg_email = st.text_input("Email", key="reg_email")
            reg_pw = st.text_input("Password", type="password", key="reg_pw")
            reg_pw2 = st.text_input("Confirm Password", type="password", key="reg_pw2")
            if st.button("Create Account", use_container_width=True, key="reg_btn"):
                if reg_pw != reg_pw2:
                    st.error("Passwords don't match")
                elif len(reg_pw) < 4:
                    st.error("Password too short")
                else:
                    try:
                        user_id = create_user(reg_email, _hash_pw(reg_pw))
                        ws_id = get_or_create_workspace(user_id)
                        st.session_state["user_id"] = user_id
                        st.session_state["user_email"] = reg_email
                        set_current_user_id(user_id)
                        set_current_workspace_id(ws_id)
                        st.success("Account created! Logging in...")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))


def render_settings():
    """Settings page — API keys and preferences."""
    st.markdown("## ⚙️ Settings")
    st.markdown("---")

    st.markdown("### 🔑 API Keys")
    providers = ["openai", "anthropic", "nvidia", "google", "deepseek"]
    for provider in providers:
        from core.config import get_key
        existing = get_key(provider)
        masked = f"{'*' * 20}{existing[-4:]}" if existing and len(existing) > 4 else ""
        new_key = st.text_input(
            f"{provider.title()} API Key",
            value="",
            placeholder=masked or f"Enter {provider} key...",
            type="password",
            key=f"key_{provider}"
        )
        if new_key and new_key != masked:
            set_key(provider, new_key)
            st.success(f"✅ {provider.title()} key saved!")

    st.markdown("---")
    st.markdown("### 🧠 Default Model")
    from core.config import DEFAULT_MODEL
    st.selectbox("Default LLM Model", AVAILABLE_MODELS,
                 index=AVAILABLE_MODELS.index(DEFAULT_MODEL) if DEFAULT_MODEL in AVAILABLE_MODELS else 0)

    st.markdown("---")
    st.markdown("### 📊 Usage Summary")
    from core.local_db import get_usage_summary
    ws_id = get_current_workspace_id()
    if ws_id:
        usage = get_usage_summary(ws_id)
        col1, col2, col3 = st.columns(3)
        col1.metric("Total API Calls", usage.get("total_calls", 0))
        col2.metric("Total Tokens", f"{usage.get('total_tokens', 0):,}")
        col3.metric("Avg Response", f"{usage.get('avg_response_ms', 0):.0f}ms")


def render_activity_logs():
    """Activity logs page."""
    st.markdown("## 📋 Activity Logs")
    st.markdown("---")
    from core.local_db import get_activity_logs
    def get_icon(t):
        return {"tool_call": "🔧", "ssh_command": "🖥️", "llm_error": "❌", "scan_complete": "🔍", "server_added": "🌐", "auto_heal": "🚑"}.get(t, "📌")
    ws_id = get_current_workspace_id()
    if ws_id:
        logs = get_activity_logs(ws_id, limit=100)
        if logs:
            for log in logs:
                icon = get_icon(log.get("event_type", ""))
                tool = f" [{log['tool_name']}]" if log.get("tool_name") else ""
                st.markdown(
                    f"{icon} **{log.get('created_at', '')[:19]}**{tool} — {log.get('detail', '')}",
                )
                if log.get("raw_output"):
                    with st.expander("Raw Output"):
                        st.code(log["raw_output"][:2000])
        else:
            st.info("No activity logged yet.")


def get_detected_tool_names() -> set:
    """Get set of tool names detected on any server."""
    ws_id = get_current_workspace_id()
    if not ws_id:
        return set()
    all_tools = get_all_detected_tools(ws_id)
    return {t["tool_name"] for t in all_tools if t["status"] in ("running", "stopped")}


def render_main():
    """Main app view with sidebar navigation."""
    inject_styles()

    # ─── Sidebar ───
    with st.sidebar:
        sidebar_header()

        # User info
        email = st.session_state.get("user_email", "")
        st.caption(f"👤 {email}")
        st.markdown("---")

        # Handle intelligent routing from Jarvis
        if "force_page" in st.session_state:
            target = st.session_state["force_page"]
            del st.session_state["force_page"]
            page_index = list(CORE_PAGES.values()).index(target) if target in CORE_PAGES.values() else 0
            st.session_state["core_nav_radio"] = list(CORE_PAGES.keys())[page_index]

        # Core pages
        page = st.radio("**Core**", list(CORE_PAGES.keys()), key="core_nav_radio", label_visibility="visible")
        selected = CORE_PAGES.get(page, "jarvis")

        st.markdown("---")

        # DevOps tool categories (collapsible)
        detected = get_detected_tool_names()

        for cat_key, cat_data in TOOL_NAV.items():
            # Count detected tools in this category
            cat_detected = [name for _, name in cat_data["items"] if name in detected]
            count_str = f" ({len(cat_detected)})" if cat_detected else ""

            with st.expander(f"{cat_data['label']}{count_str}"):
                for label, tool_name in cat_data["items"]:
                    is_detected = tool_name in detected
                    style = "" if is_detected else "opacity:0.4;"
                    status_dot = "🟢 " if is_detected else ""
                    if st.button(f"{status_dot}{label}", key=f"nav_{tool_name}",
                                 use_container_width=True):
                        st.session_state["active_tool"] = tool_name
                        st.session_state["nav_page"] = "tool"

        # Learn Mode toggle
        render_learn_mode_toggle()

        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # ─── Main Content ───
    # Check if a tool page was selected
    if st.session_state.get("nav_page") == "tool" and st.session_state.get("active_tool"):
        render_tool_page(st.session_state["active_tool"])
        # Reset nav after rendering
        st.session_state["nav_page"] = None
        return

    # Core pages — show Learn Mode explanation for the selected page
    page_name = [k for k, v in CORE_PAGES.items() if v == selected]
    if page_name:
        explain_sidebar(page_name[0])

    if selected == "jarvis":
        from ui.jarvis_view import render_infinity_core
        render_infinity_core()
    elif selected == "deploy":
        from ui.deploy_view import render_deploy_view
        render_deploy_view()
    elif selected == "drift":
        from ui.drift_view import render_drift_view
        render_drift_view()
    elif selected == "postmortem":
        from ui.postmortem_view import render_postmortem_view
        render_postmortem_view()
    elif selected == "redteam":
        from ui.redteam_view import render_redteam_view
        render_redteam_view()
    elif selected == "migrator":
        from ui.migrator_view import render_migrator_view
        render_migrator_view()
    elif selected == "finops":
        from ui.finops_view import render_finops_view
        render_finops_view()
    elif selected == "audit":
        from ui.compliance_view import render_compliance_view
        render_compliance_view()
    elif selected == "ghost":
        from ui.ghost_mode_view import render_ghost_mode
        render_ghost_mode()
    elif selected == "secrets":
        from ui.secrets_scanner_view import render_secrets_scanner
        render_secrets_scanner()
    elif selected == "dna":
        from ui.infra_dna_view import render_infra_dna
        render_infra_dna()
    elif selected == "multiterminal":
        from ui.multi_terminal_view import render_multi_terminal
        render_multi_terminal()
    elif selected == "runbooks":
        from ui.runbook_view import render_runbook_view
        render_runbook_view()
    elif selected == "warroom":
        from ui.warroom_view import render_war_room
        render_war_room()
    elif selected == "dashboard":
        render_dashboard()
    elif selected == "flow":
        from ui.pipeline_builder_view import render_pipeline_builder
        render_pipeline_builder()
    elif selected == "chat":
        render_chat_view()
    elif selected == "servers":
        render_server_view()
    elif selected == "workflow":
        render_workflow_view()
    elif selected == "settings":
        render_settings()
    elif selected == "activity_logs":
        render_activity_logs()
    else:
        render_dashboard()
