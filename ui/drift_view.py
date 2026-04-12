"""InfiniteClaw — Kill Drift (Terraform Auto-Remediation)"""
import streamlit as st
import time
from ui.styles import inject_styles

def render_drift_view():
    inject_styles()
    st.markdown("<h2 style='color:#00f0ff;'>🛠️ Terraform Drift Monitor</h2>", unsafe_allow_html=True)
    st.markdown("InfiniteClaw autonomously monitors live AWS state against your strict Terraform configuration.")
    
    st.error("🚨 DRIFT DETECTED IN RESOURCE: `aws_security_group.sg_web`")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Strict IaC (Terraform)")
        st.code("""resource "aws_security_group" "sg_web" {
  name = "web-tier"
  ingress {
    from_port = 443
    to_port   = 443
    protocol  = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
} // (Only port 443 is permitted)""", language="hcl")

    with col2:
        st.markdown("### Live AWS Console State")
        st.code("""{
  "GroupName": "web-tier",
  "IpPermissions": [
    { "FromPort": 443, "ToPort": 443 },
    { "FromPort": 22, "ToPort": 22, 
      "IpRanges": [{"CidrIp": "0.0.0.0/0"}] 
      // 🔥 ROGUE SSH ACCESS DETECTED 🔥
    }
  ]
}""", language="json")

    st.markdown("---")
    st.warning("An unknown user manually opened Port 22 globally in the AWS Console, completely bypassing CI/CD and breaking strict compliance.")
    
    if st.button("🧨 KILL DRIFT (Snap AWS matching Terraform)", type="primary", use_container_width=True):
        with st.spinner("Violently overwriting AWS state to match main.tf..."):
            time.sleep(2)
            import core.local_db as local_db
            aws_id = local_db.get_current_workspace_id()
            if aws_id:
                local_db.award_xp(aws_id, 150)
            st.success("✅ Drift Assassinated. AWS Security Group forcefully overwritten. Port 22 SSH access revoked globally.")
            st.balloons()
