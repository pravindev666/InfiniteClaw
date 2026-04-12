"""InfiniteClaw — HashiCorp Vault Adapter"""
from tools.base import DevOpsToolAdapter, DetectionResult, ToolStatus, _parse_version, _check_port

class VaultAdapter(DevOpsToolAdapter):
    name = "vault"; display_name = "HashiCorp Vault"; icon = "🔐"; category = "config_iac"; default_port = 8200
    description = "Secrets management and data protection"

    def detect(self, ssh) -> DetectionResult:
        r = self._exec(ssh, "vault version 2>/dev/null")
        if r["exit_code"] == 0:
            st_r = self._exec(ssh, "vault status -format=json 2>/dev/null")
            st = ToolStatus.RUNNING if st_r["exit_code"] in (0, 2) else ToolStatus.STOPPED
            return DetectionResult(st, _parse_version(r["stdout"]), 8200)
        return DetectionResult(ToolStatus.NOT_INSTALLED)

    def get_dashboard_data(self, ssh) -> dict:
        status = self._exec(ssh, "vault status -format=json 2>/dev/null")
        mounts = self._exec(ssh, "vault secrets list -format=json 2>/dev/null")
        return {"status": status["stdout"][:2000], "mounts": mounts["stdout"][:2000]}

    def get_tool_schemas(self):
        return [{"type":"function","function":{"name":"vault_status","description":"Get Vault seal status","parameters":{"type":"object","properties":{}}}},
                {"type":"function","function":{"name":"vault_secrets_list","description":"List secret engines","parameters":{"type":"object","properties":{}}}},
                {"type":"function","function":{"name":"vault_read","description":"Read a secret","parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}}}]

    def execute_tool_call(self, ssh, fn, args):
        if fn == "vault_status": return self._exec(ssh, "vault status 2>&1")["stdout"]
        if fn == "vault_secrets_list": return self._exec(ssh, "vault secrets list 2>&1")["stdout"]
        if fn == "vault_read": return self._exec(ssh, f"vault read {args['path']} 2>&1")["stdout"]
        return f"Unknown: {fn}"
