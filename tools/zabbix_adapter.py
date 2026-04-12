"""InfiniteClaw — Zabbix Adapter"""
from tools.base import DevOpsToolAdapter, DetectionResult, ToolStatus, _check_service, _check_port

class ZabbixAdapter(DevOpsToolAdapter):
    name = "zabbix"; display_name = "Zabbix"; icon = "📟"; category = "monitoring"; default_port = 10051
    description = "Enterprise monitoring solution"

    def detect(self, ssh) -> DetectionResult:
        svc = _check_service(ssh, "zabbix-server")
        if svc == "active":
            return DetectionResult(ToolStatus.RUNNING, None, 10051)
        if svc == "inactive": return DetectionResult(ToolStatus.STOPPED, None, 10051)
        if _check_port(ssh, 10051): return DetectionResult(ToolStatus.RUNNING, None, 10051)
        return DetectionResult(ToolStatus.NOT_INSTALLED)

    def get_dashboard_data(self, ssh) -> dict:
        status = self._exec(ssh, "systemctl status zabbix-server 2>/dev/null")
        return {"status": status["stdout"][:2000]}

    def get_tool_schemas(self):
        return [{"type":"function","function":{"name":"zabbix_status","description":"Get Zabbix server status","parameters":{"type":"object","properties":{}}}}]

    def execute_tool_call(self, ssh, fn, args):
        if fn == "zabbix_status":
            return self._exec(ssh, "systemctl status zabbix-server 2>&1")["stdout"]
        return f"Unknown: {fn}"
