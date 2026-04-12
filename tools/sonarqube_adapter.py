"""InfiniteClaw — SonarQube Adapter"""
from tools.base import DevOpsToolAdapter, DetectionResult, ToolStatus, _check_port

class SonarQubeAdapter(DevOpsToolAdapter):
    name = "sonarqube"; display_name = "SonarQube"; icon = "🛡️"; category = "security"; default_port = 9000
    description = "Code quality and security analysis"

    def detect(self, ssh) -> DetectionResult:
        r = self._exec(ssh, "curl -s http://localhost:9000/api/system/status 2>/dev/null")
        if "UP" in r["stdout"]: return DetectionResult(ToolStatus.RUNNING, None, 9000)
        if _check_port(ssh, 9000): return DetectionResult(ToolStatus.RUNNING, None, 9000)
        return DetectionResult(ToolStatus.NOT_INSTALLED)

    def get_dashboard_data(self, ssh) -> dict:
        projects = self._exec(ssh, "curl -s http://localhost:9000/api/projects/search 2>/dev/null")
        return {"projects": projects["stdout"][:3000]}

    def get_tool_schemas(self):
        return [{"type":"function","function":{"name":"sonar_projects","description":"List SonarQube projects","parameters":{"type":"object","properties":{}}}},
                {"type":"function","function":{"name":"sonar_quality_gate","description":"Get quality gate status for a project","parameters":{"type":"object","properties":{"project_key":{"type":"string"}},"required":["project_key"]}}}]

    def execute_tool_call(self, ssh, fn, args):
        if fn == "sonar_projects": return self._exec(ssh, "curl -s http://localhost:9000/api/projects/search 2>/dev/null")["stdout"]
        if fn == "sonar_quality_gate": return self._exec(ssh, f"curl -s 'http://localhost:9000/api/qualitygates/project_status?projectKey={args['project_key']}' 2>/dev/null")["stdout"]
        return f"Unknown: {fn}"
