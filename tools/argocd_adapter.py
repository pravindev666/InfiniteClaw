"""InfiniteClaw — ArgoCD Adapter"""
from tools.base import DevOpsToolAdapter, DetectionResult, ToolStatus, _parse_version, _check_binary

class ArgoCDAdapter(DevOpsToolAdapter):
    name = "argocd"
    display_name = "ArgoCD"
    icon = "🔄"
    category = "ci_cd"
    default_port = 8080
    description = "GitOps continuous delivery for Kubernetes"

    def detect(self, ssh) -> DetectionResult:
        r = self._exec(ssh, "argocd version --client 2>/dev/null")
        if r["exit_code"] == 0:
            pods = self._exec(ssh, "kubectl get pods -n argocd --no-headers 2>/dev/null | grep -c Running")
            running = int(pods["stdout"].strip() or "0") if pods["exit_code"] == 0 else 0
            st = ToolStatus.RUNNING if running > 0 else ToolStatus.STOPPED
            return DetectionResult(st, _parse_version(r["stdout"]), self.default_port, {"running_pods": running})
        return DetectionResult(ToolStatus.NOT_INSTALLED)

    def get_dashboard_data(self, ssh) -> dict:
        apps = self._exec(ssh, "argocd app list --output json 2>/dev/null")
        return {"apps": apps["stdout"][:4000]}

    def get_tool_schemas(self):
        return [{"type":"function","function":{"name":"argocd_list_apps","description":"List ArgoCD applications","parameters":{"type":"object","properties":{}}}},
                {"type":"function","function":{"name":"argocd_sync_app","description":"Sync an ArgoCD application","parameters":{"type":"object","properties":{"app_name":{"type":"string"}},"required":["app_name"]}}}]

    def execute_tool_call(self, ssh, fn, args):
        if fn == "argocd_list_apps":
            return self._exec(ssh, "argocd app list 2>/dev/null")["stdout"]
        elif fn == "argocd_sync_app":
            return self._exec(ssh, f"argocd app sync {args['app_name']} 2>/dev/null")["stdout"]
        return f"Unknown: {fn}"
