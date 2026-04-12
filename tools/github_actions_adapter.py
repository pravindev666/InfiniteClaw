"""InfiniteClaw — GitHub Actions Adapter"""
from tools.base import DevOpsToolAdapter, DetectionResult, ToolStatus, _check_binary

class GitHubActionsAdapter(DevOpsToolAdapter):
    name = "github_actions"
    display_name = "GitHub Actions"
    icon = "⚡"
    category = "ci_cd"
    default_port = 0
    description = "GitHub CI/CD workflows and self-hosted runners"

    def detect(self, ssh) -> DetectionResult:
        r = self._exec(ssh, "ls /opt/actions-runner/run.sh 2>/dev/null || ls ~/actions-runner/run.sh 2>/dev/null")
        if r["exit_code"] == 0:
            svc = self._exec(ssh, "systemctl is-active actions.runner.* 2>/dev/null")
            st = ToolStatus.RUNNING if "active" in svc["stdout"] else ToolStatus.STOPPED
            return DetectionResult(st, None, 0, {"type": "self-hosted-runner"})
        if _check_binary(ssh, "gh"):
            return DetectionResult(ToolStatus.STOPPED, None, 0, {"type": "gh-cli-only"})
        return DetectionResult(ToolStatus.NOT_INSTALLED)

    def get_dashboard_data(self, ssh) -> dict:
        runners = self._exec(ssh, "systemctl list-units 'actions.runner.*' --no-pager 2>/dev/null")
        return {"runners": runners["stdout"][:2000]}

    def get_tool_schemas(self):
        return [{"type":"function","function":{"name":"gh_actions_runner_status","description":"Check self-hosted runner status","parameters":{"type":"object","properties":{}}}}]

    def execute_tool_call(self, ssh, fn, args):
        if fn == "gh_actions_runner_status":
            return self._exec(ssh, "systemctl list-units 'actions.runner.*' --no-pager 2>/dev/null")["stdout"] or "No runners found"
        return f"Unknown: {fn}"
