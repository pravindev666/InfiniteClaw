"""InfiniteClaw — HAProxy Adapter"""
from tools.base import DevOpsToolAdapter, DetectionResult, ToolStatus, _parse_version, _check_service

class HAProxyAdapter(DevOpsToolAdapter):
    name = "haproxy"; display_name = "HAProxy"; icon = "⚖️"; category = "networking"; default_port = 8404
    description = "Load balancer and proxy server"

    def detect(self, ssh) -> DetectionResult:
        r = self._exec(ssh, "haproxy -v 2>/dev/null")
        if r["exit_code"] == 0:
            svc = _check_service(ssh, "haproxy")
            st = ToolStatus.RUNNING if svc == "active" else ToolStatus.STOPPED
            return DetectionResult(st, _parse_version(r["stdout"]), 8404)
        return DetectionResult(ToolStatus.NOT_INSTALLED)

    def get_dashboard_data(self, ssh) -> dict:
        stats = self._exec(ssh, "echo 'show stat' | socat stdio /var/run/haproxy.sock 2>/dev/null | head -30")
        return {"stats": stats["stdout"][:3000]}

    def get_tool_schemas(self):
        return [{"type":"function","function":{"name":"haproxy_stats","description":"Get HAProxy statistics","parameters":{"type":"object","properties":{}}}}]

    def execute_tool_call(self, ssh, fn, args):
        if fn == "haproxy_stats": return self._exec(ssh, "echo 'show stat' | socat stdio /var/run/haproxy.sock 2>/dev/null || curl -s http://localhost:8404/stats 2>/dev/null")["stdout"]
        return f"Unknown: {fn}"


"""InfiniteClaw — Traefik Adapter"""
class TraefikAdapter(DevOpsToolAdapter):
    name = "traefik"; display_name = "Traefik"; icon = "🚦"; category = "networking"; default_port = 8080
    description = "Cloud native reverse proxy and load balancer"

    def detect(self, ssh) -> DetectionResult:
        r = self._exec(ssh, "traefik version 2>/dev/null")
        if r["exit_code"] == 0: return DetectionResult(ToolStatus.RUNNING, _parse_version(r["stdout"]), 8080)
        from tools.base import _check_port
        if _check_port(ssh, 8080):
            api = self._exec(ssh, "curl -s http://localhost:8080/api/overview 2>/dev/null")
            if "http" in api["stdout"].lower(): return DetectionResult(ToolStatus.RUNNING, None, 8080)
        return DetectionResult(ToolStatus.NOT_INSTALLED)

    def get_dashboard_data(self, ssh) -> dict:
        overview = self._exec(ssh, "curl -s http://localhost:8080/api/overview 2>/dev/null")
        routers = self._exec(ssh, "curl -s http://localhost:8080/api/http/routers 2>/dev/null")
        return {"overview": overview["stdout"][:2000], "routers": routers["stdout"][:2000]}

    def get_tool_schemas(self):
        return [{"type":"function","function":{"name":"traefik_routers","description":"List Traefik routers","parameters":{"type":"object","properties":{}}}}]

    def execute_tool_call(self, ssh, fn, args):
        if fn == "traefik_routers": return self._exec(ssh, "curl -s http://localhost:8080/api/http/routers 2>/dev/null")["stdout"]
        return f"Unknown: {fn}"
