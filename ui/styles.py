"""
InfiniteClaw — UI Styles
Premium glassmorphic infinity theme CSS injection.
"""
import streamlit as st

INFINITECLAW_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;900&family=JetBrains+Mono:wght@400;500;700&display=swap');

:root {
    --bg-primary: #0a0e17;
    --bg-secondary: #111827;
    --bg-card: rgba(17, 24, 39, 0.7);
    --bg-glass: rgba(15, 23, 42, 0.6);
    --border-glass: rgba(0, 240, 255, 0.15);
    --cyan: #00f0ff;
    --purple: #a855f7;
    --green: #22c55e;
    --yellow: #eab308;
    --red: #ef4444;
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --gradient-main: linear-gradient(135deg, #00f0ff 0%, #a855f7 100%);
}

/* ─── Global ─── */
.stApp {
    background: var(--bg-primary) !important;
    font-family: 'Inter', sans-serif !important;
    color: var(--text-primary) !important;
}

.stApp > header { background: transparent !important; }

/* ─── Sidebar ─── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1321 0%, #111827 50%, #0d1321 100%) !important;
    border-right: 1px solid var(--border-glass) !important;
}

[data-testid="stSidebar"] .stRadio label {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.85rem !important;
    padding: 8px 12px !important;
    border-radius: 8px !important;
    transition: all 0.3s ease !important;
    margin: 2px 0 !important;
}

[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(0, 240, 255, 0.08) !important;
    transform: translateX(3px) !important;
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
    color: var(--cyan) !important;
    font-weight: 700 !important;
}

/* ─── Cards ─── */
.glass-card {
    background: var(--bg-glass) !important;
    backdrop-filter: blur(20px) !important;
    border: 1px solid var(--border-glass) !important;
    border-radius: 16px !important;
    padding: 20px !important;
    margin: 8px 0 !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
    transition: all 0.3s ease !important;
}

.glass-card:hover {
    border-color: rgba(0, 240, 255, 0.3) !important;
    box-shadow: 0 8px 32px rgba(0, 240, 255, 0.1) !important;
    transform: translateY(-2px) !important;
}

/* ─── Status Indicators ─── */
.status-running { color: var(--green); font-weight: 600; }
.status-stopped { color: var(--yellow); font-weight: 600; }
.status-error { color: var(--red); font-weight: 600; }
.status-not-installed { color: var(--text-secondary); }

@keyframes pulse-green {
    0%, 100% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.4); }
    50% { box-shadow: 0 0 0 8px rgba(34, 197, 94, 0); }
}

.pulse-indicator {
    display: inline-block;
    width: 10px; height: 10px;
    border-radius: 50%;
    animation: pulse-green 2s infinite;
}
.pulse-green { background: var(--green); animation: pulse-green 2s infinite; }

@keyframes pulse-red {
    0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
    50% { box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
}
.pulse-red { background: var(--red); animation: pulse-red 2s infinite; }

/* ─── Metric Cards ─── */
.metric-card {
    background: var(--bg-glass);
    backdrop-filter: blur(20px);
    border: 1px solid var(--border-glass);
    border-radius: 12px;
    padding: 16px;
    text-align: center;
}

.metric-value {
    font-size: 2rem;
    font-weight: 900;
    background: var(--gradient-main);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.metric-label {
    font-size: 0.75rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 4px;
}

/* ─── Chat ─── */
.chat-msg-user {
    background: rgba(0, 240, 255, 0.08);
    border: 1px solid rgba(0, 240, 255, 0.2);
    border-radius: 12px 12px 4px 12px;
    padding: 12px 16px;
    margin: 8px 0;
}

.chat-msg-ai {
    background: rgba(168, 85, 247, 0.08);
    border: 1px solid rgba(168, 85, 247, 0.2);
    border-radius: 12px 12px 12px 4px;
    padding: 12px 16px;
    margin: 8px 0;
}

/* ─── Tool Grid ─── */
.tool-grid-item {
    background: var(--bg-glass);
    border: 1px solid var(--border-glass);
    border-radius: 12px;
    padding: 16px;
    text-align: center;
    transition: all 0.3s ease;
    cursor: pointer;
}

.tool-grid-item:hover {
    border-color: var(--cyan);
    transform: scale(1.02);
}

.tool-icon { font-size: 2rem; margin-bottom: 8px; }
.tool-name { font-size: 0.85rem; font-weight: 600; color: var(--text-primary); }
.tool-version { font-size: 0.7rem; color: var(--text-secondary); font-family: 'JetBrains Mono', monospace; }

/* ─── Buttons ─── */
.stButton > button {
    background: var(--gradient-main) !important;
    color: #0a0e17 !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 8px 24px !important;
    transition: all 0.3s ease !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 20px rgba(0, 240, 255, 0.3) !important;
}

/* ─── Inputs ─── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border-glass) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
    font-family: 'JetBrains Mono', monospace !important;
}

.stSelectbox > div > div {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border-glass) !important;
}

/* ─── Dividers ─── */
hr { border-color: var(--border-glass) !important; }

/* ─── Expanders (Category Headers) ─── */
.streamlit-expanderHeader {
    background: rgba(0, 240, 255, 0.05) !important;
    border: 1px solid var(--border-glass) !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    color: var(--cyan) !important;
}

/* ─── Logo Header ─── */
.infiniteclaw-header {
    text-align: center;
    padding: 10px 0;
}

.infiniteclaw-title {
    font-size: 1.4rem;
    font-weight: 900;
    background: var(--gradient-main);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: 2px;
}

.infiniteclaw-subtitle {
    font-size: 0.65rem;
    color: var(--text-secondary);
    letter-spacing: 3px;
    text-transform: uppercase;
}

/* ─── Scrollbar ─── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: rgba(0, 240, 255, 0.2); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(0, 240, 255, 0.4); }

/* ─── Greyed Out Tool ─── */
.tool-greyed {
    opacity: 0.35;
    pointer-events: none;
}
</style>
"""


def inject_styles():
    """Inject the InfiniteClaw theme into the Streamlit page."""
    st.markdown(INFINITECLAW_CSS, unsafe_allow_html=True)


def sidebar_header():
    """Render the branded sidebar header."""
    st.markdown("""
    <div class="infiniteclaw-header">
        <div class="infiniteclaw-title">∞ INFINITECLAW</div>
        <div class="infiniteclaw-subtitle">DevOps AI Command Center</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")


def metric_card(label: str, value: str, col=None):
    """Render a glassmorphic metric card."""
    html = f"""
    <div class="metric-card">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """
    if col:
        col.markdown(html, unsafe_allow_html=True)
    else:
        st.markdown(html, unsafe_allow_html=True)


def status_badge(status: str) -> str:
    """Return HTML for a status badge."""
    icons = {"running": "🟢", "stopped": "🟡", "not_installed": "🔴", "error": "❌", "unknown": "⚪"}
    labels = {"running": "RUNNING", "stopped": "STOPPED", "not_installed": "NOT INSTALLED", "error": "ERROR", "unknown": "UNKNOWN"}
    css_class = f"status-{status.replace(' ', '-')}"
    return f'<span class="{css_class}">{icons.get(status, "⚪")} {labels.get(status, status.upper())}</span>'
