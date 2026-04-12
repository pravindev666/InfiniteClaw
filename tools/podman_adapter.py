"""InfiniteClaw — Podman Adapter"""
from tools.base import DevOpsToolAdapter, DetectionResult, ToolStatus, _parse_version, _check_binary

class PodmanAdapter(DevOpsToolAdapter):
    name = "podman"; display_name = "Podman"; icon = "🦭"; category = "containers"; default_port = 0
    description = "Rootless container engine"

    def detect(self, ssh) -> DetectionResult:
        r = self._exec(ssh, "podman --version 2>/dev/null")
        if r["exit_code"] == 0:
            info = self._exec(ssh, "podman info --format '{{.Host.Os}}' 2>/dev/null")
            st = ToolStatus.RUNNING if info["exit_code"] == 0 else ToolStatus.STOPPED
            return DetectionResult(st, _parse_version(r["stdout"]))
        return DetectionResult(ToolStatus.NOT_INSTALLED)

    def get_dashboard_data(self, ssh) -> dict:
        ps = self._exec(ssh, "podman ps --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}' 2>/dev/null")
        pods = self._exec(ssh, "podman pod list 2>/dev/null")
        return {"containers": ps["stdout"][:2000], "pods": pods["stdout"][:1000]}

    def get_tool_schemas(self):
        return [{"type":"function","function":{"name":"podman_ps","description":"List Podman containers","parameters":{"type":"object","properties":{"all":{"type":"boolean"}}}}}]

    def execute_tool_call(self, ssh, fn, args):
        if fn == "podman_ps":
            a = "-a" if args.get("all") else ""
            return self._exec(ssh, f"podman ps {a} 2>&1")["stdout"]
        return f"Unknown: {fn}"
