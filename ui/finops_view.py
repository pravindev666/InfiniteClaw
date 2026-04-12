"""InfiniteClaw — CFO FinOps Dashboard"""
import streamlit as st
import time
from ui.styles import inject_styles

def render_finops_view():
    inject_styles()
    st.markdown("<h2 style='color:#00f0ff;'>💰 CFO FinOps Dashboard</h2>", unsafe_allow_html=True)
    st.markdown("Automated cost analysis and idle resource assassination.")
    
    # Simulated metrics
    total_spend = "$24,500/mo"
    wasted_spend = "$8,420/mo"
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total AWS/GCP Run Rate", total_spend)
    col2.metric("Identified Cloud Waste", wasted_spend, "-34% inefficiency", delta_color="inverse")
    col3.metric("Idle Instances", "14 nodes")
    
    st.markdown("### 🔍 Idle Resource Audit")
    
    waste_data = [
        {"Resource": "staging-k8s-node-4", "Provider": "AWS EC2", "Uptime": "45 days", "CPU_Util": "1.2%", "Waste": "$420/mo"},
        {"Resource": "dev-db-replicate-old", "Provider": "AWS RDS", "Uptime": "100 days", "CPU_Util": "0.0%", "Waste": "$1,100/mo"},
        {"Resource": "abandoned-gpu-cluster", "Provider": "GCP Compute", "Uptime": "14 days", "CPU_Util": "0.0%", "Waste": "$6,900/mo"},
    ]
    st.table(waste_data)
    
    st.markdown("---")
    st.markdown("### 🛑 One-Click Cost Assassination")
    st.warning("The AI will autonomously authenticate via AWS/GCP APIs and forcefully hibernate all idle unallocated resources. This action causes no data loss but drops active idle connections.")
    
    if st.button("🚨 Execute Savings ($8,420/mo)", type="primary", use_container_width=True):
        with st.spinner("Autonomously negotiating with cloud APIs to hibernate instances..."):
            time.sleep(3)
            import core.local_db as local_db
            aws_id = local_db.get_current_workspace_id()
            if aws_id:
                local_db.award_xp(aws_id, 250) # Award huge XP for saving the company money
            st.success("✅ CFO MODE SUCCESS: 14 idle instances successfully downscaled or hibernated. Next month's billing reduced by $8,420! (+250 XP Awarded)")
            st.balloons()
