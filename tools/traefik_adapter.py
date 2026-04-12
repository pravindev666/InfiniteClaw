"""InfiniteClaw — Traefik Adapter"""
from tools.base import DevOpsToolAdapter, DetectionResult, ToolStatus, _parse_version, _check_port

class TraefikAdapter(DevOpsToolAdapter):
    name = "traefik"; display_name = "Traefik"; icon = "🚦"; category = "networking"; default_port = 8080
    description = "Cloud native reverse proxy"

    def detect(self, ssh) -> DetectionResult:
        r = self._exec(ssh, "traefik version 2>/dev/null")
        if r["exit_code"] == 0: return DetectionResult(ToolStatus.RUNNING, _parse_version(r["stdout"]), 8080)
        if _check_port(ssh, 8080):
            api = self._exec(ssh, "curl -s http://localhost:8080/api/overview 2>/dev/null")
            if "http" in api["stdout"].lower(): return DetectionResult(ToolStatus.RUNNING, None, 8080)
        return DetectionResult(ToolStatus.NOT_INSTALLED)

    def get_dashboard_data(self, ssh) -> dict:
        overview = self._exec(ssh, "curl -s http://localhost:8080/api/overview 2>/dev/null")
        routers = self._exec(ssh, "curl -s http://localhost:8080/api/http/routers 2>/dev/null")
        return {"overview": overview["stdout"][:2000], "routers": routers["stdout"][:2000]}

    def get_tool_schemas(self):
        return [{"type":"function","function":{"name":"traefik_overview","description":"Get Traefik overview","parameters":{"type":"object","properties":{}}}},
                {"type":"function","function":{"name":"traefik_routers","description":"List HTTP routers","parameters":{"type":"object","properties":{}}}}]

    def execute_tool_call(self, ssh, fn, args):
        if fn == "traefik_overview": return self._exec(ssh, "curl -s http://localhost:8080/api/overview 2>/dev/null")["stdout"]
        if fn == "traefik_routers": return self._exec(ssh, "curl -s http://localhost:8080/api/http/routers 2>/dev/null")["stdout"]
        return f"Unknown: {fn}"
