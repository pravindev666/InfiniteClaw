"""InfiniteClaw — Packer Adapter"""
from tools.base import DevOpsToolAdapter, DetectionResult, ToolStatus, _parse_version

class PackerAdapter(DevOpsToolAdapter):
    name = "packer"; display_name = "Packer"; icon = "📦"; category = "config_iac"; default_port = 0
    description = "Machine image builder"

    def detect(self, ssh) -> DetectionResult:
        r = self._exec(ssh, "packer --version 2>/dev/null")
        if r["exit_code"] == 0: return DetectionResult(ToolStatus.RUNNING, _parse_version(r["stdout"]))
        return DetectionResult(ToolStatus.NOT_INSTALLED)

    def get_dashboard_data(self, ssh) -> dict:
        return {"info": "Packer is a CLI tool — use AI chat to build and validate templates"}

    def get_tool_schemas(self):
        return [{"type":"function","function":{"name":"packer_validate","description":"Validate a Packer template","parameters":{"type":"object","properties":{"template":{"type":"string","description":"Path to template file"}},"required":["template"]}}},
                {"type":"function","function":{"name":"packer_build","description":"Build a Packer template","parameters":{"type":"object","properties":{"template":{"type":"string"}},"required":["template"]}}}]

    def execute_tool_call(self, ssh, fn, args):
        if fn == "packer_validate": return self._exec(ssh, f"packer validate {args['template']} 2>&1")["stdout"]
        if fn == "packer_build": return self._exec(ssh, f"packer build {args['template']} 2>&1", timeout=300)["stdout"]
        return f"Unknown: {fn}"
