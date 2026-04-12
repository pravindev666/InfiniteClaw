"""InfiniteClaw — Terraform Adapter"""
from tools.base import DevOpsToolAdapter, DetectionResult, ToolStatus, _parse_version, _check_binary

class TerraformAdapter(DevOpsToolAdapter):
    name = "terraform"; display_name = "Terraform"; icon = "🏗️"; category = "config_iac"; default_port = 0
    description = "Infrastructure as Code provisioning"

    def detect(self, ssh) -> DetectionResult:
        r = self._exec(ssh, "terraform --version 2>/dev/null")
        if r["exit_code"] == 0:
            return DetectionResult(ToolStatus.RUNNING, _parse_version(r["stdout"]))
        return DetectionResult(ToolStatus.NOT_INSTALLED)

    def get_dashboard_data(self, ssh) -> dict:
        ws = self._exec(ssh, "terraform workspace list 2>/dev/null")
        state = self._exec(ssh, "terraform state list 2>/dev/null | head -50")
        return {"workspaces": ws["stdout"][:1000], "state": state["stdout"][:3000]}

    def get_tool_schemas(self):
        return [{"type":"function","function":{"name":"terraform_plan","description":"Run terraform plan","parameters":{"type":"object","properties":{"dir":{"type":"string","description":"Working directory"}}}}},
                {"type":"function","function":{"name":"terraform_apply","description":"Run terraform apply (auto-approve)","parameters":{"type":"object","properties":{"dir":{"type":"string"}}}}},
                {"type":"function","function":{"name":"terraform_state_list","description":"List resources in state","parameters":{"type":"object","properties":{"dir":{"type":"string"}}}}},
                {"type":"function","function":{"name":"terraform_output","description":"Show terraform outputs","parameters":{"type":"object","properties":{"dir":{"type":"string"}}}}}]

    def execute_tool_call(self, ssh, fn, args):
        d = f"-chdir={args['dir']}" if args.get("dir") else ""
        if fn == "terraform_plan":
            return self._exec(ssh, f"terraform {d} plan -no-color 2>&1", timeout=120)["stdout"]
        elif fn == "terraform_apply":
            return self._exec(ssh, f"terraform {d} apply -auto-approve -no-color 2>&1", timeout=300)["stdout"]
        elif fn == "terraform_state_list":
            return self._exec(ssh, f"terraform {d} state list 2>&1")["stdout"]
        elif fn == "terraform_output":
            return self._exec(ssh, f"terraform {d} output -json 2>&1")["stdout"]
        return f"Unknown: {fn}"
