"""InfiniteClaw — Grafana Adapter"""
from tools.base import DevOpsToolAdapter, DetectionResult, ToolStatus, _parse_version, _check_service, _check_port

class GrafanaAdapter(DevOpsToolAdapter):
    name = "grafana"; display_name = "Grafana"; icon = "📊"; category = "monitoring"; default_port = 3000
    description = "Monitoring dashboards and visualization"

    def detect(self, ssh) -> DetectionResult:
        svc = _check_service(ssh, "grafana-server")
        if svc == "active" or _check_port(ssh, 3000):
            r = self._exec(ssh, "curl -s http://localhost:3000/api/health 2>/dev/null")
            return DetectionResult(ToolStatus.RUNNING, _parse_version(r["stdout"]), 3000)
        r = self._exec(ssh, "grafana-server -v 2>/dev/null")
        if r["exit_code"] == 0: return DetectionResult(ToolStatus.STOPPED, _parse_version(r["stdout"]), 3000)
        return DetectionResult(ToolStatus.NOT_INSTALLED)

    def get_dashboard_data(self, ssh) -> dict:
        dashboards = self._exec(ssh, "curl -s http://admin:admin@localhost:3000/api/search?type=dash-db 2>/dev/null")
        datasources = self._exec(ssh, "curl -s http://admin:admin@localhost:3000/api/datasources 2>/dev/null")
        return {"dashboards": dashboards["stdout"][:3000], "datasources": datasources["stdout"][:1000]}

    def get_tool_schemas(self):
        return [{"type":"function","function":{"name":"grafana_dashboards","description":"List Grafana dashboards","parameters":{"type":"object","properties":{}}}},
                {"type":"function","function":{"name":"grafana_datasources","description":"List Grafana datasources","parameters":{"type":"object","properties":{}}}}]

    def execute_tool_call(self, ssh, fn, args):
        if fn == "grafana_dashboards":
            return self._exec(ssh, "curl -s http://admin:admin@localhost:3000/api/search?type=dash-db 2>/dev/null")["stdout"]
        elif fn == "grafana_datasources":
            return self._exec(ssh, "curl -s http://admin:admin@localhost:3000/api/datasources 2>/dev/null")["stdout"]
        return f"Unknown: {fn}"
