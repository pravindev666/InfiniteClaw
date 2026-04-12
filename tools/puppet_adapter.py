"""InfiniteClaw — Puppet Adapter"""
from tools.base import DevOpsToolAdapter, DetectionResult, ToolStatus, _parse_version, _check_service

class PuppetAdapter(DevOpsToolAdapter):
    name = "puppet"
    display_name = "Puppet"
    icon = "🧵"
    category = "config_iac"
    default_port = 8140
    description = "Configuration management and orchestration"

    def detect(self, ssh) -> DetectionResult:
        r = self._exec(ssh, "puppet --version 2>/dev/null")
        if r["exit_code"] == 0:
            svc = _check_service(ssh, "puppetserver")
            st = ToolStatus.RUNNING if svc == "active" else ToolStatus.STOPPED
            return DetectionResult(st, _parse_version(r["stdout"]), 8140)
        return DetectionResult(ToolStatus.NOT_INSTALLED)

    def get_dashboard_data(self, ssh) -> dict:
        status = self._exec(ssh, "puppet status 2>/dev/null || systemctl status puppetserver 2>/dev/null")
        modules = self._exec(ssh, "puppet module list 2>/dev/null")
        return {"status": status["stdout"][:2000], "modules": modules["stdout"][:2000]}

    def get_tool_schemas(self):
        return [{"type":"function","function":{"name":"puppet_status","description":"Get Puppet server status","parameters":{"type":"object","properties":{}}}},
                {"type":"function","function":{"name":"puppet_modules","description":"List installed Puppet modules","parameters":{"type":"object","properties":{}}}}]

    def execute_tool_call(self, ssh, fn, args):
        if fn == "puppet_status":
            return self._exec(ssh, "systemctl status puppetserver 2>&1 || puppet --version")["stdout"]
        if fn == "puppet_modules":
            return self._exec(ssh, "puppet module list 2>&1")["stdout"]
        return f"Unknown: {fn}"
