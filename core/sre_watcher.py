"""InfiniteClaw — Autonomous SRE Watcher"""
import time
import logging
import threading
from core.local_db import get_servers, get_server_tools, upsert_server_tool, get_current_workspace_id
from core.ssh_manager import ssh_manager
from tools.tool_router import tool_router

logger = logging.getLogger("SRE_Watcher")

class SREWatcher(threading.Thread):
    def __init__(self, check_interval: int = 60):
        super().__init__(daemon=True)
        self.check_interval = check_interval
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def run(self):
        logger.info("🛡️ Autonomous SRE Watcher Started")
        while not self._stop_event.is_set():
            self._run_health_checks()
            time.sleep(self.check_interval)

    def _run_health_checks(self):
        """Scans known tools on servers and checks availability."""
        ws_id = get_current_workspace_id()
        if not ws_id:
            return

        servers = get_servers(ws_id)
        for server in servers:
            if self._stop_event.is_set():
                break

            tools = get_server_tools(server["id"])
            for t in tools:
                adapter = tool_router.get_adapter(t["tool_name"])
                if not adapter:
                    continue
                
                old_status = t["status"]
                
                # Check status via SSH
                ssh = ssh_manager.get_connection(server["id"])
                if not ssh:
                    continue

                detection = adapter.detect(ssh)
                upsert_server_tool(server["id"], adapter.name, detection.status.value, detection.version)

                # Simulated Auto-Healing Logic:
                # If a service was running but is suddenly NOT running, attempt to heal
                if old_status == "running" and detection.status.value in ["stopped", "error"]:
                    logger.warning(f"🚨 SRE ALERT: {adapter.name} crashed on {server['name']}. Attempting auto-heal...")
                    
                    # Example heal: try to restart docker containers or systemd services dynamically
                    heal_command = f"sudo systemctl restart {adapter.name} || docker restart {adapter.name}"
                    ssh_manager.execute_command(server["id"], heal_command)
                    
                    # Re-verify
                    time.sleep(2)
                    re_detect = adapter.detect(ssh)
                    if re_detect.status.value == "running":
                        import core.local_db as db
                        db.award_xp(server['workspace_id'], 50) # Award some auto-heal XP to root user
                        db.log_activity(
                            ws_id, "auto_heal",
                            detail=f"Successfully auto-healed {adapter.name} via systemctl/docker restart.",
                            tool_name=adapter.name, server_id=server["id"]
                        )
                        upsert_server_tool(server["id"], adapter.name, "running", re_detect.version)
                        logger.info(f"✅ SRE WATCHER: Successfully auto-healed {adapter.name}!")
