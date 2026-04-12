"""InfiniteClaw — Consul Adapter"""
from tools.base import DevOpsToolAdapter, DetectionResult, ToolStatus, _parse_version, _check_port

class ConsulAdapter(DevOpsToolAdapter):
    name = "consul"
    display_name = "Consul"
    icon = "🗺️"
    category = "config_iac"
    default_port = 8500
    description = "Service discovery and mesh"

    def detect(self, ssh) -> DetectionResult:
        r = self._exec(ssh, "consul version 2>/dev/null")
        if r["exit_code"] == 0:
            members = self._exec(ssh, "consul members 2>/dev/null")
            st = ToolStatus.RUNNING if members["exit_code"] == 0 else ToolStatus.STOPPED
            return DetectionResult(st, _parse_version(r["stdout"]), 8500)
        return DetectionResult(ToolStatus.NOT_INSTALLED)

    def get_dashboard_data(self, ssh) -> dict:
        members = self._exec(ssh, "consul members 2>/dev/null")
        services = self._exec(ssh, "consul catalog services 2>/dev/null")
        return {"members": members["stdout"][:2000], "services": services["stdout"][:2000]}

    def get_tool_schemas(self):
        return [
            {"type": "function", "function": {"name": "consul_members", "description": "List Consul cluster members", "parameters": {"type": "object", "properties": {}}}},
            {"type": "function", "function": {"name": "consul_services", "description": "List registered services", "parameters": {"type": "object", "properties": {}}}}
        ]

    def execute_tool_call(self, ssh, fn, args):
        if fn == "consul_members":
            return self._exec(ssh, "consul members 2>&1")["stdout"]
        if fn == "consul_services":
            return self._exec(ssh, "consul catalog services 2>&1")["stdout"]
        return f"Unknown: {fn}"
