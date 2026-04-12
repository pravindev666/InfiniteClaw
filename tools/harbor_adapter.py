"""InfiniteClaw — Harbor Registry Adapter"""
from tools.base import DevOpsToolAdapter, DetectionResult, ToolStatus, _check_port

class HarborAdapter(DevOpsToolAdapter):
    name = "harbor"; display_name = "Harbor Registry"; icon = "🏗️"; category = "containers"; default_port = 443
    description = "Container image registry with vulnerability scanning"

    def detect(self, ssh) -> DetectionResult:
        r = self._exec(ssh, "docker compose -f /opt/harbor/docker-compose.yml ps 2>/dev/null || ls /opt/harbor 2>/dev/null")
        if "harbor" in r["stdout"].lower() or r["exit_code"] == 0:
            api = self._exec(ssh, "curl -sk https://localhost/api/v2.0/health 2>/dev/null")
            st = ToolStatus.RUNNING if "healthy" in api["stdout"].lower() else ToolStatus.STOPPED
            return DetectionResult(st, None, 443)
        return DetectionResult(ToolStatus.NOT_INSTALLED)

    def get_dashboard_data(self, ssh) -> dict:
        projects = self._exec(ssh, "curl -sk https://localhost/api/v2.0/projects 2>/dev/null")
        return {"projects": projects["stdout"][:3000]}

    def get_tool_schemas(self):
        return [{"type":"function","function":{"name":"harbor_projects","description":"List Harbor projects","parameters":{"type":"object","properties":{}}}}]

    def execute_tool_call(self, ssh, fn, args):
        if fn == "harbor_projects":
            return self._exec(ssh, "curl -sk https://localhost/api/v2.0/projects 2>/dev/null")["stdout"]
        return f"Unknown: {fn}"
