"""InfiniteClaw — GitLab CI Adapter"""
from tools.base import DevOpsToolAdapter, DetectionResult, ToolStatus, _parse_version, _check_service, _check_port

class GitLabAdapter(DevOpsToolAdapter):
    name = "gitlab"
    display_name = "GitLab CI"
    icon = "🦊"
    category = "ci_cd"
    default_port = 443
    description = "DevOps platform with built-in CI/CD"

    def detect(self, ssh) -> DetectionResult:
        svc = _check_service(ssh, "gitlab-runsvdir")
        if svc == "active":
            r = self._exec(ssh, "gitlab-rake gitlab:env:info 2>/dev/null | head -5")
            return DetectionResult(ToolStatus.RUNNING, _parse_version(r["stdout"]), 443)
        r = self._exec(ssh, "gitlab-ctl status 2>/dev/null")
        if r["exit_code"] == 0 and "run:" in r["stdout"]:
            return DetectionResult(ToolStatus.RUNNING, None, 443)
        if r["exit_code"] == 0:
            return DetectionResult(ToolStatus.STOPPED)
        return DetectionResult(ToolStatus.NOT_INSTALLED)

    def get_dashboard_data(self, ssh) -> dict:
        status = self._exec(ssh, "gitlab-ctl status 2>/dev/null")
        runners = self._exec(ssh, "gitlab-runner list 2>/dev/null")
        return {"services": status["stdout"][:2000], "runners": runners["stdout"][:1000]}

    def get_tool_schemas(self):
        return [{"type":"function","function":{"name":"gitlab_status","description":"Get GitLab service status","parameters":{"type":"object","properties":{}}}},
                {"type":"function","function":{"name":"gitlab_runners","description":"List GitLab CI runners","parameters":{"type":"object","properties":{}}}}]

    def execute_tool_call(self, ssh, fn, args):
        if fn == "gitlab_status":
            return self._exec(ssh, "gitlab-ctl status")["stdout"]
        elif fn == "gitlab_runners":
            return self._exec(ssh, "gitlab-runner list 2>&1")["stdout"]
        return f"Unknown: {fn}"
