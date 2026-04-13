"""InfiniteClaw — Real Post-Mortem Synthesizer
Feeds ACTUAL SRE Watcher auto-heal logs from the activity database
into the LLM to generate real incident reports — not hardcoded templates.
"""
import streamlit as st
import time
from datetime import datetime
from ui.styles import inject_styles
from core.local_db import get_current_workspace_id, _get_connection, award_xp


def get_real_incidents(ws_id: str, limit: int = 20):
    conn = _get_connection()
    c = conn.cursor()
    c.execute(
        """SELECT * FROM activity_logs 
           WHERE workspace_id = ? AND event_type IN ('auto_heal', 'llm_error', 'tool_call')
           ORDER BY created_at DESC LIMIT ?""",
        (ws_id, limit)
    )
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def render_postmortem_view():
    inject_styles()
    st.markdown("<h2 style='color:#00f0ff;'>Automated Incident Post-Mortems</h2>", unsafe_allow_html=True)
    st.markdown("Generate real blameless post-mortems from actual SRE Watcher logs — not templates.")

    ws_id = get_current_workspace_id()
    if not ws_id:
        st.warning("No active workspace.")
        return

    incidents = get_real_incidents(ws_id)

    if not incidents:
        st.info("No incidents recorded yet. When the SRE Watcher auto-heals a crash or the AI executes tool calls, they will appear here.")
        st.markdown("---")
        st.markdown("### Demo Mode")
        st.markdown("Since no real incidents exist yet, you can generate a sample post-mortem to see the format.")
        if st.button("Generate Sample Post-Mortem", type="primary"):
            _generate_sample_postmortem()
        return

    # Show real incidents
    st.markdown("### Recent Activity for Post-Mortem")
    heal_events = [i for i in incidents if i["event_type"] == "auto_heal"]
    error_events = [i for i in incidents if i["event_type"] == "llm_error"]

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Events", len(incidents))
    col2.metric("Auto-Heals", len(heal_events))
    col3.metric("Errors", len(error_events))

    # Select events to include in post-mortem
    st.markdown("### Select Events to Include")
    selected = []
    for i, inc in enumerate(incidents[:10]):
        icon = "🚑" if inc["event_type"] == "auto_heal" else "🔧" if inc["event_type"] == "tool_call" else "❌"
        if st.checkbox(f"{icon} [{inc['created_at']}] {inc['event_type']} — {inc['detail'][:60]}", key=f"inc_{i}"):
            selected.append(inc)

    if selected and st.button("Synthesize Post-Mortem from Selected Events", type="primary", use_container_width=True):
        with st.spinner("AI is analyzing real incident data and synthesizing a report..."):
            try:
                from core.llm_engine import engine
                event_data = "\n".join([
                    f"[{e['created_at']}] TYPE={e['event_type']} TOOL={e.get('tool_name','N/A')} "
                    f"DETAIL={e['detail']} OUTPUT={e.get('raw_output','')[:300]}"
                    for e in selected
                ])
                prompt = (
                    "You are a senior SRE writing a formal 'Blameless Post-Mortem' report. "
                    "Based on the following REAL incident logs from our infrastructure monitoring system, "
                    "write a professional post-mortem with these sections:\n"
                    "1. Executive Summary\n"
                    "2. Timeline of Events\n"
                    "3. Root Cause Analysis (Five Whys)\n"
                    "4. Impact Assessment\n"
                    "5. Action Items\n\n"
                    f"INCIDENT LOGS:\n{event_data}"
                )
                report = engine.quick_ask(prompt)
                
                award_xp(ws_id, 50)
                
                st.success("Post-Mortem synthesized from real data!")
                st.download_button(
                    label="Download Post-Mortem (Markdown)",
                    data=report,
                    file_name=f"PostMortem_{datetime.now().strftime('%Y-%m-%d_%H%M')}.md",
                    mime="text/markdown"
                )
                with st.expander("Preview Document", expanded=True):
                    st.markdown(report)
                    
            except Exception as e:
                st.error(f"AI synthesis failed: {e}. Ensure your LLM API key is configured in Settings.")
    elif not selected:
        st.caption("Select at least one event above, then click 'Synthesize'.")


def _generate_sample_postmortem():
    """Fallback demo when no real incidents exist."""
    report = f"""# Blameless Incident Post-Mortem

**System**: InfiniteClaw Cluster
**Date**: {datetime.now().strftime("%Y-%m-%d")}
**Status**: DEMO — No real incidents recorded yet

## Executive Summary
This is a sample post-mortem. Once your SRE Watcher detects real crashes and auto-heals them, 
those events will be fed directly to the AI to generate real, data-driven reports.

## How This Will Work
1. SRE Watcher detects a service crash (e.g., Nginx returns 502)
2. It auto-heals by restarting the service
3. The event is logged to `activity_logs`
4. You come here, select the events, and the AI writes the full report

*Connect a server and let InfiniteClaw run to generate real incident data.*
"""
    st.download_button(
        label="Download Sample Post-Mortem",
        data=report,
        file_name=f"Sample_PostMortem_{datetime.now().strftime('%Y-%m-%d')}.md",
        mime="text/markdown"
    )
    with st.expander("Preview", expanded=True):
        st.markdown(report)
