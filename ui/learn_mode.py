"""InfiniteClaw — Learn Mode System
Global toggle that adds plain-English explanations to every section
of the UI, making the platform understandable for complete beginners.
"""
import streamlit as st

# ─── Plain English Explanations for Every Feature ───
EXPLANATIONS = {
    # Sidebar nav items
    "Infinity Core": "This is your home screen. Think of it like the main menu of a video game — it shows your level, badges, and lets you type commands in plain English.",
    "Code-to-Cloud": "Got a folder of code (like a Python app)? Drop it here as a .zip file and the AI will automatically figure out how to package and run it on a server. No manual setup needed.",
    "Terraform Drift": "Terraform is a tool that defines your servers in code. 'Drift' means someone changed a server manually without updating the code. This page catches those sneaky changes.",
    "Post-Mortems": "When a server crashes, engineers write a report explaining what went wrong. This page auto-writes that report using AI — saving hours of work.",
    "AI Red Team": "A 'Red Team' tries to hack your own systems to find weaknesses BEFORE real hackers do. This page runs automated security attacks on your test servers.",
    "DB Auto-Migrator": "Changing a database structure (like adding a new column) can break things. This page generates safe SQL commands that won't crash your database.",
    "CFO FinOps": "This page checks if you're wasting money on servers. It connects to your machines and checks if CPU/memory is being used or just sitting idle.",
    "SOC2 Auditor": "SOC2 is a security certification that companies need. This page auto-checks if your servers meet the security standards.",
    "Ghost Mode": "Every single command that InfiniteClaw has ever run on your servers is recorded here. It's like a security camera for your infrastructure.",
    "Secrets Scanner": "This connects to your servers and hunts for exposed passwords, API keys, and insecure settings that hackers could exploit.",
    "Infra DNA": "Takes a 'fingerprint' of your server — what's installed, what ports are open, how much disk space is left. You can compare fingerprints over time to spot unauthorized changes.",
    "Multi-Terminal": "Type one command and run it on ALL your servers at the same time. Like having 10 terminal windows open at once, but in one screen.",
    "Runbooks": "A runbook is a checklist of commands to run in order (like 'update packages → restart services → check health'). Save them once, run them with one click forever.",
    "War Room": "When something is broken RIGHT NOW, this is your emergency screen. It pulls live data from the crashing server and asks AI to diagnose the problem.",
    "Dashboard": "A visual overview of all your connected servers and the tools running on them. Like a scoreboard for your infrastructure.",
    "Flow Builder": "A drag-and-drop visual editor for creating deployment pipelines. Think of it like building a flowchart that actually runs commands.",
    "Chat": "Talk to the AI assistant about your infrastructure. Ask it questions like 'How much disk space is left on server-1?' and it will check for you.",
    "Remote Servers": "This is where you add your servers. You need a server's IP address, username, and password (or SSH key) to connect.",
    "CI/CD Workflow": "CI/CD stands for 'Continuous Integration / Continuous Deployment'. It means automatically testing and deploying code whenever you push changes.",
    "Settings": "Change your AI model, API keys, and other configuration options.",

    # Common UI elements
    "ssh_key": "An SSH key is like a digital password file. Instead of typing a password every time, your computer uses this file to prove who you are. '.pem' and '.ppk' are two different formats of these key files.",
    "api_key": "An API key is a secret code that lets InfiniteClaw talk to AI services like OpenAI (ChatGPT). You get one by signing up at the AI provider's website.",
    "docker": "Docker is a tool that packages your app and everything it needs into a 'container' — like a portable box that runs the same way everywhere.",
    "kubernetes": "Kubernetes (K8s) manages many Docker containers across many servers. Think of Docker as a shipping container, and Kubernetes as the entire shipping port.",
    "terraform": "Terraform lets you define your entire server setup in code files. Instead of clicking buttons in AWS, you write code that creates servers automatically.",
    "nginx": "Nginx is a web server — it's the program that receives web requests from the internet and sends back your website or API responses.",
    "ssh": "SSH (Secure Shell) is a way to remotely control a Linux server through the command line. It's like Remote Desktop, but for text commands only.",
    "sre": "SRE stands for 'Site Reliability Engineering'. An SRE's job is to keep websites and servers running smoothly 24/7.",
    "llm": "LLM stands for 'Large Language Model' — it's the AI brain (like ChatGPT) that powers InfiniteClaw's intelligence.",
}


def is_learn_mode_on() -> bool:
    """Check if Learn Mode is currently enabled."""
    return st.session_state.get("learn_mode", False)


def render_learn_mode_toggle():
    """Render the Learn Mode toggle in the sidebar."""
    st.sidebar.markdown("---")
    learn_on = st.sidebar.toggle(
        "Learn Mode",
        value=st.session_state.get("learn_mode", False),
        key="learn_mode_toggle",
        help="Turn on plain-English explanations for every feature"
    )
    st.session_state["learn_mode"] = learn_on
    if learn_on:
        st.sidebar.caption("Learn Mode ON — hover over sections for plain-English explanations")


def explain(key: str):
    """Show an explanation callout if Learn Mode is on."""
    if not is_learn_mode_on():
        return
    text = EXPLANATIONS.get(key)
    if text:
        st.info(f"**What is this?** {text}", icon="💡")


def explain_inline(key: str) -> str:
    """Return explanation text for use in tooltips/help params."""
    return EXPLANATIONS.get(key, "")


def explain_sidebar(page_name: str):
    """Show a brief explanation under the page title when Learn Mode is on."""
    if not is_learn_mode_on():
        return
    text = EXPLANATIONS.get(page_name)
    if text:
        st.markdown(
            f"<div style='background: rgba(0,240,255,0.08); border-left: 3px solid #00f0ff; "
            f"padding: 10px 15px; border-radius: 5px; margin-bottom: 15px; font-size: 0.85rem; color: #94a3b8;'>"
            f"💡 <b>Learn Mode:</b> {text}</div>",
            unsafe_allow_html=True
        )
