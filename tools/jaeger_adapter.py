"""InfiniteClaw — Jaeger Adapter"""
from tools.base import DevOpsToolAdapter, DetectionResult, ToolStatus, _check_port

class JaegerAdapter(DevOpsToolAdapter):
    name = "jaeger"; display_name = "Jaeger"; icon = "🔬"; category = "monitoring"; default_port = 16686
    description = "Distributed tracing system"

    def detect(self, ssh) -> DetectionResult:
        if _check_port(ssh, 16686):
            r = self._exec(ssh, "curl -s http://localhost:16686/api/services 2>/dev/null")
            return DetectionResult(ToolStatus.RUNNING, None, 16686)
        r = self._exec(ssh, "which jaeger-all-in-one 2>/dev/null || docker ps --filter name=jaeger --format '{{.Names}}' 2>/dev/null")
        if r["exit_code"] == 0 and r["stdout"].strip():
            return DetectionResult(ToolStatus.STOPPED, None, 16686)
        return DetectionResult(ToolStatus.NOT_INSTALLED)

    def get_dashboard_data(self, ssh) -> dict:
        services = self._exec(ssh, "curl -s http://localhost:16686/api/services 2>/dev/null")
        return {"services": services["stdout"][:2000]}

    def get_tool_schemas(self):
        return [{"type":"function","function":{"name":"jaeger_services","description":"List traced services","parameters":{"type":"object","properties":{}}}},
                {"type":"function","function":{"name":"jaeger_traces","description":"Search traces for a service","parameters":{"type":"object","properties":{"service":{"type":"string"},"limit":{"type":"integer"}},"required":["service"]}}}]

    def execute_tool_call(self, ssh, fn, args):
        if fn == "jaeger_services":
            return self._exec(ssh, "curl -s http://localhost:16686/api/services 2>/dev/null")["stdout"]
        elif fn == "jaeger_traces":
            lim = args.get("limit", 20)
            return self._exec(ssh, f"curl -s 'http://localhost:16686/api/traces?service={args['service']}&limit={lim}' 2>/dev/null")["stdout"]
        return f"Unknown: {fn}"
