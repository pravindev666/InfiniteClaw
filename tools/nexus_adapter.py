"""InfiniteClaw — Nexus Artifactory Adapter"""
from tools.base import DevOpsToolAdapter, DetectionResult, ToolStatus, _check_port

class NexusAdapter(DevOpsToolAdapter):
    name = "nexus"; display_name = "Nexus Artifactory"; icon = "📦"; category = "data"; default_port = 8081
    description = "Repository manager for artifacts"

    def detect(self, ssh) -> DetectionResult:
        r = self._exec(ssh, "curl -s http://localhost:8081/service/rest/v1/status 2>/dev/null")
        if r["exit_code"] == 0 and r["stdout"].strip():
            return DetectionResult(ToolStatus.RUNNING, None, 8081)
        if _check_port(ssh, 8081): return DetectionResult(ToolStatus.RUNNING, None, 8081)
        return DetectionResult(ToolStatus.NOT_INSTALLED)

    def get_dashboard_data(self, ssh) -> dict:
        repos = self._exec(ssh, "curl -s http://localhost:8081/service/rest/v1/repositories 2>/dev/null")
        return {"repositories": repos["stdout"][:3000]}

    def get_tool_schemas(self):
        return [{"type":"function","function":{"name":"nexus_repos","description":"List Nexus repositories","parameters":{"type":"object","properties":{}}}},
                {"type":"function","function":{"name":"nexus_status","description":"Get Nexus system status","parameters":{"type":"object","properties":{}}}}]

    def execute_tool_call(self, ssh, fn, args):
        if fn == "nexus_repos": return self._exec(ssh, "curl -s http://localhost:8081/service/rest/v1/repositories 2>/dev/null")["stdout"]
        if fn == "nexus_status": return self._exec(ssh, "curl -s http://localhost:8081/service/rest/v1/status 2>/dev/null")["stdout"]
        return f"Unknown: {fn}"
