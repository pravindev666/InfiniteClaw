"""InfiniteClaw — Splunk Adapter"""
from tools.base import DevOpsToolAdapter, DetectionResult, ToolStatus, _parse_version, _check_port

class SplunkAdapter(DevOpsToolAdapter):
    name = "splunk"; display_name = "Splunk"; icon = "🔍"; category = "monitoring"; default_port = 8089
    description = "Log management and SIEM platform"

    def detect(self, ssh) -> DetectionResult:
        r = self._exec(ssh, "/opt/splunk/bin/splunk version 2>/dev/null || splunk version 2>/dev/null")
        if r["exit_code"] == 0:
            status = self._exec(ssh, "/opt/splunk/bin/splunk status 2>/dev/null || splunk status 2>/dev/null")
            st = ToolStatus.RUNNING if "running" in status["stdout"].lower() else ToolStatus.STOPPED
            return DetectionResult(st, _parse_version(r["stdout"]), 8089)
        return DetectionResult(ToolStatus.NOT_INSTALLED)

    def get_dashboard_data(self, ssh) -> dict:
        indexes = self._exec(ssh, "curl -sk https://localhost:8089/services/data/indexes -u admin:changeme --output - 2>/dev/null | head -100")
        return {"indexes": indexes["stdout"][:3000]}

    def get_tool_schemas(self):
        return [{"type":"function","function":{"name":"splunk_search","description":"Run a Splunk SPL search","parameters":{"type":"object","properties":{"query":{"type":"string","description":"SPL query"}},"required":["query"]}}},
                {"type":"function","function":{"name":"splunk_status","description":"Get Splunk service status","parameters":{"type":"object","properties":{}}}}]

    def execute_tool_call(self, ssh, fn, args):
        if fn == "splunk_search":
            return self._exec(ssh, f"/opt/splunk/bin/splunk search '{args['query']}' -maxout 50 2>/dev/null", timeout=60)["stdout"]
        elif fn == "splunk_status":
            return self._exec(ssh, "/opt/splunk/bin/splunk status 2>/dev/null || splunk status 2>/dev/null")["stdout"]
        return f"Unknown: {fn}"
