"""InfiniteClaw — Infinity Core Landing Page"""
import streamlit as st
from ui.styles import inject_styles
from core.local_db import get_current_user_id, get_user_gamification

INFINITY_CSS = """
<style>
/* Pulsing Neon Core */
.infinity-core-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    margin-top: 40px;
    margin-bottom: 40px;
}

.neon-ring {
    width: 150px;
    height: 150px;
    border-radius: 50%;
    background: transparent;
    border: 4px solid var(--cyan);
    box-shadow: 0 0 20px var(--cyan), inset 0 0 20px var(--cyan);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 4rem;
    font-weight: 900;
    color: var(--cyan);
    animation: rotate-pulse 4s infinite linear;
    position: relative;
}

.neon-text {
    position: absolute;
    font-family: 'Inter', sans-serif;
    animation: counter-rotate 4s infinite linear;
}

@keyframes rotate-pulse {
    0% { transform: rotate(0deg); box-shadow: 0 0 10px var(--cyan), inset 0 0 10px var(--cyan); }
    50% { transform: rotate(180deg); box-shadow: 0 0 40px var(--purple), inset 0 0 40px var(--purple); border-color: var(--purple); }
    100% { transform: rotate(360deg); box-shadow: 0 0 10px var(--cyan), inset 0 0 10px var(--cyan); border-color: var(--cyan);}
}

@keyframes counter-rotate {
    0% { transform: rotate(0deg); color: var(--cyan); }
    50% { transform: rotate(-180deg); color: var(--purple); }
    100% { transform: rotate(-360deg); color: var(--cyan); }
}

/* Magic Buttons */
.magic-btn-container {
    display: flex;
    gap: 15px;
    justify-content: center;
    margin-top: 20px;
    flex-wrap: wrap;
}

.magic-btn {
    background: rgba(15, 23, 42, 0.7);
    border: 1px solid var(--border-glass);
    padding: 15px 25px;
    border-radius: 12px;
    color: white;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    backdrop-filter: blur(10px);
}

.magic-btn:hover {
    background: var(--gradient-main);
    transform: translateY(-3px);
    color: #000;
    box-shadow: 0 5px 25px rgba(0, 240, 255, 0.4);
}

/* XP Bar */
.xp-container {
    width: 100%;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 10px;
    height: 12px;
    margin-top: 5px;
    position: relative;
    overflow: hidden;
}
.xp-fill {
    height: 100%;
    background: var(--gradient-main);
    border-radius: 10px;
    transition: width 1s ease-in-out;
}
</style>
"""

def render_infinity_core():
    inject_styles()
    st.markdown(INFINITY_CSS, unsafe_allow_html=True)
    
    user_id = get_current_user_id()
    gamification = get_user_gamification(user_id) if user_id else {"xp": 0, "level": 1, "badges": []}
    
    # Header & Gamification
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown(f"### 👑 Lv.{gamification['level']} Architect")
    with col2:
        xp_modulo = gamification['xp'] % 1000
        prc = int((xp_modulo / 1000) * 100)
        st.markdown(f"<div style='text-align:right; font-size:0.8rem; color:#94a3b8;'>{xp_modulo} / 1000 XP (Next Rank)</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='xp-container'><div class='xp-fill' style='width: {prc}%;'></div></div>", unsafe_allow_html=True)

    
    # Badges Showcase
    if gamification['badges']:
        b_html = " ".join([f"<span title='{b['badge_name']}' style='font-size:1.5rem;'>{b['badge_icon']}</span>" for b in gamification['badges']])
        st.markdown(f"<div style='margin-bottom: 20px;'>**Badges:** {b_html}</div>", unsafe_allow_html=True)

    st.markdown("---")
    
    # Glowing Core
    st.markdown("""
    <div class="infinity-core-container">
        <div class="neon-ring">
            <div class="neon-text">∞</div>
        </div>
        <h2 style="margin-top: 30px; font-weight: 900; letter-spacing: 1px;">Hello, Commander.</h2>
        <p style="color: var(--text-secondary); text-align: center;">What infrastructure shall we build today?</p>
    </div>
    """, unsafe_allow_html=True)

    # Magic Chat Input
    prompt = st.chat_input("E.g., Deploy a highly available Minecraft Server on my AWS instances...")
    if prompt:
        st.session_state["infinity_prompt"] = prompt
        st.rerun()

    # If the user typed a prompt
    if st.session_state.get("infinity_prompt"):
        st.markdown(f"<div class='glass-card'><b>⚡ Initiating Protocol:</b> {st.session_state['infinity_prompt']}</div>", unsafe_allow_html=True)
        st.info("I am transitioning you to the Interactive Flow Builder to execute this architecture...")
        # Auto-switch view conceptually (handled by the actual LLM if fully integrated, here simulating transition)
        import time
        time.sleep(1.5)
        st.session_state["force_page"] = "flow"
        st.session_state["infinity_prompt"] = None
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Magic Buttons
    st.markdown("""
    <div class="magic-btn-container">
        <div class="magic-btn" onclick="document.querySelector('input').value='Analyze all log files for errors.'; document.dispatchEvent(new Event('input'))">🚑 Auto-Heal Systems</div>
        <div class="magic-btn">🧠 Train on Docs</div>
        <div class="magic-btn">🌩️ One-Click Matrix Deploy</div>
    </div>
    """, unsafe_allow_html=True)

