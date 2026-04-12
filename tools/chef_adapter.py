"""InfiniteClaw — Chef Adapter"""
from tools.base import DevOpsToolAdapter, DetectionResult, ToolStatus, _parse_version, _check_binary

class ChefAdapter(DevOpsToolAdapter):
    name = "chef"; display_name = "Chef"; icon = "🍳"; category = "config_iac"; default_port = 443
    description = "Infrastructure automation and configuration"

    def detect(self, ssh) -> DetectionResult:
        r = self._exec(ssh, "chef-client --version 2>/dev/null")
        if r["exit_code"] == 0:
            return DetectionResult(ToolStatus.RUNNING, _parse_version(r["stdout"]))
        r = self._exec(ssh, "knife --version 2>/dev/null")
        if r["exit_code"] == 0:
            return DetectionResult(ToolStatus.RUNNING, _parse_version(r["stdout"]))
        return DetectionResult(ToolStatus.NOT_INSTALLED)

    def get_dashboard_data(self, ssh) -> dict:
        nodes = self._exec(ssh, "knife node list 2>/dev/null")
        cookbooks = self._exec(ssh, "knife cookbook list 2>/dev/null")
        return {"nodes": nodes["stdout"][:2000], "cookbooks": cookbooks["stdout"][:2000]}

    def get_tool_schemas(self):
        return [{"type":"function","function":{"name":"chef_nodes","description":"List Chef nodes","parameters":{"type":"object","properties":{}}}},
                {"type":"function","function":{"name":"chef_cookbooks","description":"List cookbooks","parameters":{"type":"object","properties":{}}}}]

    def execute_tool_call(self, ssh, fn, args):
        if fn == "chef_nodes": return self._exec(ssh, "knife node list 2>&1")["stdout"]
        if fn == "chef_cookbooks": return self._exec(ssh, "knife cookbook list 2>&1")["stdout"]
        return f"Unknown: {fn}"
