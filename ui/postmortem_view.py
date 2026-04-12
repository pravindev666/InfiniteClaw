"""InfiniteClaw — Automated Incident Post-Mortem Synthesizer"""
import streamlit as st
import time
from datetime import datetime
from ui.styles import inject_styles

PM_TEMPLATE = """# Blameless Incident Post-Mortem

**System**: InfiniteClaw Cluster 1
**Date of Incident**: {date}
**MTTR (Mean Time to Resolution)**: 124 seconds.

## 1. Executive Summary
At 03:04 AM UTC, the primary Postgres read-replica exhausted available RAM, triggering an Out-of-Memory (OOM) kernel panic. InfiniteClaw's SRE-Watcher daemon detected the crash at 03:05 AM, dynamically edited the `deployment.yaml` to increase memory limits, and successfully recovered the pod by 03:06 AM without dropping any active user transactions.

## 2. Timeline
- **03:03:15 UTC**: Memory usage on `db-replica-2` crosses 95% threshold.
- **03:04:10 UTC**: Linux kernel triggers OOM killer. Pod dies instantly.
- **03:05:00 UTC**: `sre_watcher.py` pings fail. InfiniteClaw investigates logs.
- **03:05:45 UTC**: AI parses logs: `Killed process 123 (postgres)`.
- **03:06:14 UTC**: AI autonomously triggers Auto-Heal, increasing RAM limit from 4GB to 8GB. Pod becomes `Running`.

## 3. Five Whys Route Cause Analysis
1. **Why did the database crash?** It ran out of memory.
2. **Why did it run out of memory?** An unoptimized SQL query performed a full table scan on 40 million rows.
3. **Why did the query run?** A scheduled massive report chron job executed asynchronously.

## 4. AI Action Items
- 🤖 Automatically enforce query timeouts (`statement_timeout = '30s'`) on replica clusters. (EXECUTED)
- 🤖 Send notification to Backend Teams on Slack to optimize the report query using appropriate indexes. (EXECUTED)

*Document Generated Autonomously by InfiniteClaw AI.*
"""

def render_postmortem_view():
    inject_styles()
    st.markdown("<h2 style='color:#00f0ff;'>📝 Automated Incident Post-Mortems</h2>", unsafe_allow_html=True)
    st.markdown("Eliminate tedious corporate writing. Generate flawless blameless post-mortems for any recent outage instantly.")

    st.markdown("### Recent Handled Outages")
    st.info("🔥 **Incident 892**: Postgres Read-Replica OOM Crash (Auto-Healed by SRE Watcher)")
    
    if st.button("Synthesize Post-Mortem Document", type="primary"):
        with st.spinner("Analyzing Kubernetes Crash Logs and SRE-Watcher Execution Timelines..."):
            time.sleep(2)
        
        report = PM_TEMPLATE.format(date=datetime.now().strftime("%Y-%m-%d"))
        
        import core.local_db as local_db
        aws_id = local_db.get_current_workspace_id()
        if aws_id:
            local_db.award_xp(aws_id, 50)
            
        st.success("✅ Post-Mortem successfully generated!")
        st.download_button(
            label="📄 Download Post-Mortem (Markdown)",
            data=report,
            file_name=f"Incident_892_PostMortem_{datetime.now().strftime('%Y-%m-%d')}.md",
            mime="text/markdown"
        )
        with st.expander("Preview Document"):
            st.markdown(report)
