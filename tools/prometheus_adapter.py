"""InfiniteClaw — Prometheus Adapter"""
from tools.base import DevOpsToolAdapter, DetectionResult, ToolStatus, _parse_version, _check_service, _check_port

class PrometheusAdapter(DevOpsToolAdapter):
    name = "prometheus"; display_name = "Prometheus"; icon = "📡"; category = "monitoring"; default_port = 9090
    description = "Metrics collection and alerting"

    def detect(self, ssh) -> DetectionResult:
        svc = _check_service(ssh, "prometheus")
        if svc == "active" or _check_port(ssh, 9090):
            r = self._exec(ssh, "curl -s http://localhost:9090/api/v1/status/buildinfo 2>/dev/null")
            return DetectionResult(ToolStatus.RUNNING, _parse_version(r["stdout"]), 9090)
        r = self._exec(ssh, "prometheus --version 2>/dev/null")
        if r["exit_code"] == 0:
            return DetectionResult(ToolStatus.STOPPED, _parse_version(r["stdout"]), 9090)
        return DetectionResult(ToolStatus.NOT_INSTALLED)

    def get_dashboard_data(self, ssh) -> dict:
        targets = self._exec(ssh, "curl -s http://localhost:9090/api/v1/targets?state=active 2>/dev/null")
        alerts = self._exec(ssh, "curl -s http://localhost:9090/api/v1/alerts 2>/dev/null")
        return {"targets": targets["stdout"][:4000], "alerts": alerts["stdout"][:2000]}

    def get_tool_schemas(self):
        return [{"type":"function","function":{"name":"prometheus_query","description":"Execute a PromQL query","parameters":{"type":"object","properties":{"query":{"type":"string","description":"PromQL expression"}},"required":["query"]}}},
                {"type":"function","function":{"name":"prometheus_targets","description":"List scrape targets","parameters":{"type":"object","properties":{}}}}]

    def execute_tool_call(self, ssh, fn, args):
        if fn == "prometheus_query":
            import urllib.parse
            q = urllib.parse.quote(args["query"])
            return self._exec(ssh, f"curl -s 'http://localhost:9090/api/v1/query?query={q}' 2>/dev/null")["stdout"]
        elif fn == "prometheus_targets":
            return self._exec(ssh, "curl -s http://localhost:9090/api/v1/targets 2>/dev/null")["stdout"]
        return f"Unknown: {fn}"
