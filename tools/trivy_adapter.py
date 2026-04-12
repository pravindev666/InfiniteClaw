"""InfiniteClaw — Trivy Adapter"""
from tools.base import DevOpsToolAdapter, DetectionResult, ToolStatus, _parse_version, _check_binary

class TrivyAdapter(DevOpsToolAdapter):
    name = "trivy"; display_name = "Trivy"; icon = "🔍"; category = "security"; default_port = 0
    description = "Container and filesystem vulnerability scanner"

    def detect(self, ssh) -> DetectionResult:
        r = self._exec(ssh, "trivy --version 2>/dev/null")
        if r["exit_code"] == 0: return DetectionResult(ToolStatus.RUNNING, _parse_version(r["stdout"]))
        return DetectionResult(ToolStatus.NOT_INSTALLED)

    def get_dashboard_data(self, ssh) -> dict:
        return {"info": "Trivy is a CLI scanner — use AI chat to scan images and repos"}

    def get_tool_schemas(self):
        return [{"type":"function","function":{"name":"trivy_scan_image","description":"Scan a container image for vulnerabilities","parameters":{"type":"object","properties":{"image":{"type":"string"}},"required":["image"]}}},
                {"type":"function","function":{"name":"trivy_scan_fs","description":"Scan filesystem for vulnerabilities","parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}}}]

    def execute_tool_call(self, ssh, fn, args):
        if fn == "trivy_scan_image": return self._exec(ssh, f"trivy image --severity HIGH,CRITICAL {args['image']} 2>&1", timeout=120)["stdout"]
        if fn == "trivy_scan_fs": return self._exec(ssh, f"trivy fs --severity HIGH,CRITICAL {args['path']} 2>&1", timeout=120)["stdout"]
        return f"Unknown: {fn}"
