"""InfiniteClaw — Helm Adapter"""
from tools.base import DevOpsToolAdapter, DetectionResult, ToolStatus, _parse_version, _check_binary

class HelmAdapter(DevOpsToolAdapter):
    name = "helm"; display_name = "Helm"; icon = "⎈"; category = "containers"; default_port = 0
    description = "Kubernetes package manager"

    def detect(self, ssh) -> DetectionResult:
        r = self._exec(ssh, "helm version --short 2>/dev/null")
        if r["exit_code"] == 0:
            return DetectionResult(ToolStatus.RUNNING, _parse_version(r["stdout"]))
        return DetectionResult(ToolStatus.NOT_INSTALLED)

    def get_dashboard_data(self, ssh) -> dict:
        releases = self._exec(ssh, "helm list --all-namespaces --output table 2>/dev/null")
        repos = self._exec(ssh, "helm repo list 2>/dev/null")
        return {"releases": releases["stdout"][:3000], "repos": repos["stdout"][:1000]}

    def get_tool_schemas(self):
        return [{"type":"function","function":{"name":"helm_list","description":"List Helm releases","parameters":{"type":"object","properties":{"namespace":{"type":"string"}}}}},
                {"type":"function","function":{"name":"helm_install","description":"Install a Helm chart","parameters":{"type":"object","properties":{"release":{"type":"string"},"chart":{"type":"string"},"namespace":{"type":"string"},"values":{"type":"string","description":"YAML values"}},"required":["release","chart"]}}}]

    def execute_tool_call(self, ssh, fn, args):
        if fn == "helm_list":
            ns = f"-n {args['namespace']}" if args.get("namespace") else "-A"
            return self._exec(ssh, f"helm list {ns} 2>&1")["stdout"]
        elif fn == "helm_install":
            ns = f"-n {args.get('namespace','default')}"
            return self._exec(ssh, f"helm install {args['release']} {args['chart']} {ns} 2>&1", timeout=120)["stdout"]
        return f"Unknown: {fn}"
