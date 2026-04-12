"""InfiniteClaw — Nagios Adapter"""
from tools.base import DevOpsToolAdapter, DetectionResult, ToolStatus, _check_service, _check_port

class NagiosAdapter(DevOpsToolAdapter):
    name = "nagios"; display_name = "Nagios"; icon = "👁️"; category = "monitoring"; default_port = 80
    description = "Infrastructure monitoring and alerting"

    def detect(self, ssh) -> DetectionResult:
        svc = _check_service(ssh, "nagios")
        if svc == "active":
            r = self._exec(ssh, "nagios --version 2>/dev/null | head -2")
            return DetectionResult(ToolStatus.RUNNING, None, 80)
        if svc == "inactive": return DetectionResult(ToolStatus.STOPPED)
        r = self._exec(ssh, "ls /etc/nagios/ 2>/dev/null || ls /usr/local/nagios/ 2>/dev/null")
        if r["exit_code"] == 0: return DetectionResult(ToolStatus.STOPPED)
        return DetectionResult(ToolStatus.NOT_INSTALLED)

    def get_dashboard_data(self, ssh) -> dict:
        status = self._exec(ssh, "cat /var/log/nagios/status.dat 2>/dev/null | head -200")
        return {"status": status["stdout"][:3000]}

    def get_tool_schemas(self):
        return [{"type":"function","function":{"name":"nagios_status","description":"Get Nagios service status","parameters":{"type":"object","properties":{}}}}]

    def execute_tool_call(self, ssh, fn, args):
        if fn == "nagios_status":
            return self._exec(ssh, "systemctl status nagios 2>&1")["stdout"]
        return f"Unknown: {fn}"
