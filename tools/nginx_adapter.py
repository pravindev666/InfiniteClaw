"""InfiniteClaw — Nginx Adapter"""
from tools.base import DevOpsToolAdapter, DetectionResult, ToolStatus, _parse_version, _check_service

class NginxAdapter(DevOpsToolAdapter):
    name = "nginx"; display_name = "Nginx"; icon = "🌐"; category = "networking"; default_port = 80
    description = "Web server and reverse proxy"

    def detect(self, ssh) -> DetectionResult:
        r = self._exec(ssh, "nginx -v 2>&1")
        if "nginx" in r["stderr"].lower() or "nginx" in r["stdout"].lower():
            svc = _check_service(ssh, "nginx")
            st = ToolStatus.RUNNING if svc == "active" else ToolStatus.STOPPED
            version = _parse_version(r["stderr"] + r["stdout"])
            return DetectionResult(st, version, 80)
        return DetectionResult(ToolStatus.NOT_INSTALLED)

    def get_dashboard_data(self, ssh) -> dict:
        status = self._exec(ssh, "systemctl status nginx 2>/dev/null")
        sites = self._exec(ssh, "ls /etc/nginx/sites-enabled/ 2>/dev/null || ls /etc/nginx/conf.d/ 2>/dev/null")
        conns = self._exec(ssh, "curl -s http://localhost/nginx_status 2>/dev/null")
        return {"status": status["stdout"][:1000], "sites": sites["stdout"][:1000], "connections": conns["stdout"][:500]}

    def get_tool_schemas(self):
        return [{"type":"function","function":{"name":"nginx_test_config","description":"Test Nginx configuration","parameters":{"type":"object","properties":{}}}},
                {"type":"function","function":{"name":"nginx_reload","description":"Reload Nginx configuration","parameters":{"type":"object","properties":{}}}},
                {"type":"function","function":{"name":"nginx_list_sites","description":"List enabled sites","parameters":{"type":"object","properties":{}}}}]

    def execute_tool_call(self, ssh, fn, args):
        if fn == "nginx_test_config": return self._exec(ssh, "nginx -t 2>&1")["stderr"] + self._exec(ssh, "nginx -t 2>&1")["stdout"]
        if fn == "nginx_reload": return self._exec(ssh, "systemctl reload nginx 2>&1")["stdout"] or "Nginx reloaded"
        if fn == "nginx_list_sites": return self._exec(ssh, "ls -la /etc/nginx/sites-enabled/ 2>/dev/null || ls -la /etc/nginx/conf.d/ 2>/dev/null")["stdout"]
        return f"Unknown: {fn}"
