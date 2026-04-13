"""InfiniteClaw — Secrets Scanner
SSH-based security scanner that checks for exposed secrets, insecure configs,
and dangerous permissions on connected servers. Makes SOC2 compliance REAL.
"""
import streamlit as st
import time
from ui.styles import inject_styles
from core.local_db import get_current_workspace_id, get_servers, award_xp
from core.ssh_manager import ssh_manager


SCAN_CHECKS = [
    {
        "id": "env_files",
        "name": "Exposed .env Files",
        "severity": "CRITICAL",
        "command": "find /home /var/www /opt /srv -name '.env' -readable 2>/dev/null | head -20",
        "bad_if": lambda out: bool(out.strip()),
        "remedy": "Move .env files outside the web root and restrict permissions: chmod 600 .env"
    },
    {
        "id": "root_containers",
        "name": "Docker Containers Running as Root",
        "severity": "HIGH",
        "command": "docker ps -q 2>/dev/null | xargs -I {} docker inspect --format '{{.Name}} {{.Config.User}}' {} 2>/dev/null | grep -v -E ':[0-9]' | head -20",
        "bad_if": lambda out: bool(out.strip()),
        "remedy": "Set USER directive in Dockerfiles. Never run containers as root in production."
    },
    {
        "id": "world_readable",
        "name": "World-Readable Config Files",
        "severity": "HIGH",
        "command": "find /etc -name '*.conf' -perm -o=r -type f 2>/dev/null | head -20",
        "bad_if": lambda out: len(out.strip().split('\n')) > 10,
        "remedy": "Restrict config file permissions: chmod 640 /etc/*.conf"
    },
    {
        "id": "ssh_no_passphrase",
        "name": "SSH Keys Without Passphrase",
        "severity": "CRITICAL",
        "command": "find /home -name 'id_rsa' -o -name 'id_ed25519' 2>/dev/null | while read f; do ssh-keygen -y -P '' -f \"$f\" >/dev/null 2>&1 && echo \"UNPROTECTED: $f\"; done",
        "bad_if": lambda out: "UNPROTECTED" in out,
        "remedy": "Re-generate SSH keys with a passphrase: ssh-keygen -p -f <key>"
    },
    {
        "id": "open_ports",
        "name": "Unexpected Open Ports",
        "severity": "MEDIUM",
        "command": "ss -tlnp 2>/dev/null | grep LISTEN | awk '{print $4}' | sort",
        "bad_if": lambda out: False,  # Always informational
        "remedy": "Review and close unnecessary ports with ufw or iptables."
    },
    {
        "id": "failed_logins",
        "name": "Recent Failed SSH Login Attempts",
        "severity": "MEDIUM",
        "command": "grep 'Failed password' /var/log/auth.log 2>/dev/null | tail -10 || journalctl -u sshd --no-pager -n 10 2>/dev/null | grep -i fail",
        "bad_if": lambda out: bool(out.strip()),
        "remedy": "Consider installing fail2ban or restricting SSH to key-only auth."
    },
    {
        "id": "unattended_upgrades",
        "name": "Automatic Security Updates Disabled",
        "severity": "MEDIUM",
        "command": "dpkg -l unattended-upgrades 2>/dev/null | grep -q '^ii' && echo 'ENABLED' || echo 'DISABLED'",
        "bad_if": lambda out: "DISABLED" in out,
        "remedy": "Enable automatic security patches: apt install unattended-upgrades"
    },
]


def render_secrets_scanner():
    inject_styles()
    st.markdown("<h2 style='color:#ef4444;'>Secrets Scanner — Real Security Audit</h2>", unsafe_allow_html=True)
    st.markdown("SSH into your servers and scan for exposed secrets, dangerous permissions, and insecure configurations.")

    ws_id = get_current_workspace_id()
    if not ws_id:
        st.warning("No active workspace.")
        return

    servers = get_servers(ws_id)
    if not servers:
        st.info("No servers connected. Add a server in Remote Servers first.")
        return

    server_names = {s["name"]: s["id"] for s in servers}
    selected_server = st.selectbox("Select Target Server", list(server_names.keys()))

    if st.button("Launch Security Scan", type="primary", use_container_width=True):
        server_id = server_names[selected_server]
        findings = []

        with st.status("Scanning for secrets and vulnerabilities...", expanded=True) as status:
            for check in SCAN_CHECKS:
                st.write(f"Checking: **{check['name']}**...")
                try:
                    result = ssh_manager.execute_on_server(server_id, check["command"], timeout=15)
                    output = result.get("stdout", "")
                    is_bad = check["bad_if"](output)
                    findings.append({
                        "name": check["name"],
                        "severity": check["severity"],
                        "vulnerable": is_bad,
                        "output": output,
                        "remedy": check["remedy"]
                    })
                except Exception as e:
                    findings.append({
                        "name": check["name"],
                        "severity": check["severity"],
                        "vulnerable": False,
                        "output": f"Scan error: {e}",
                        "remedy": check["remedy"]
                    })

            status.update(label="Scan Complete", state="complete", expanded=False)

        # Results
        st.markdown("---")
        st.markdown("### Scan Results")

        vulns = [f for f in findings if f["vulnerable"]]
        clean = [f for f in findings if not f["vulnerable"]]

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Checks", len(findings))
        col2.metric("Vulnerabilities Found", len(vulns), delta=f"-{len(vulns)}" if vulns else "0", delta_color="inverse")
        col3.metric("Passed", len(clean))

        if vulns:
            st.error(f"**{len(vulns)} security issue(s) found!**")
            for f in vulns:
                severity_color = {"CRITICAL": "red", "HIGH": "orange", "MEDIUM": "yellow"}.get(f["severity"], "white")
                with st.expander(f"🔴 [{f['severity']}] {f['name']}", expanded=True):
                    st.code(f["output"][:2000], language="bash")
                    st.warning(f"**Remedy**: {f['remedy']}")
        else:
            st.success("No critical vulnerabilities found on this scan.")
            award_xp(ws_id, 100)

        if clean:
            st.markdown("### Passed Checks")
            for f in clean:
                with st.expander(f"🟢 {f['name']}"):
                    if f["output"].strip():
                        st.code(f["output"][:1000], language="bash")
                    else:
                        st.markdown("Clean — no findings.")
