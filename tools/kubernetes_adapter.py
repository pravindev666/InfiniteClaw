"""InfiniteClaw — Kubernetes Adapter"""
from tools.base import DevOpsToolAdapter, DetectionResult, ToolStatus, _parse_version, _check_binary

class KubernetesAdapter(DevOpsToolAdapter):
    name = "kubernetes"
    display_name = "Kubernetes"
    icon = "☸️"
    category = "containers"
    default_port = 6443
    description = "Container orchestration platform"

    def detect(self, ssh) -> DetectionResult:
        r = self._exec(ssh, "kubectl version --client --short 2>/dev/null || kubectl version --client 2>/dev/null")
        if r["exit_code"] == 0:
            cluster = self._exec(ssh, "kubectl cluster-info 2>/dev/null")
            st = ToolStatus.RUNNING if cluster["exit_code"] == 0 and "running" in cluster["stdout"].lower() else ToolStatus.STOPPED
            return DetectionResult(st, _parse_version(r["stdout"]), self.default_port)
        return DetectionResult(ToolStatus.NOT_INSTALLED)

    def get_dashboard_data(self, ssh) -> dict:
        nodes = self._exec(ssh, "kubectl get nodes -o wide --no-headers 2>/dev/null")
        pods = self._exec(ssh, "kubectl get pods --all-namespaces --no-headers 2>/dev/null | head -50")
        svcs = self._exec(ssh, "kubectl get svc --all-namespaces --no-headers 2>/dev/null")
        deploys = self._exec(ssh, "kubectl get deployments --all-namespaces --no-headers 2>/dev/null")
        return {"nodes": nodes["stdout"][:2000], "pods": pods["stdout"][:3000],
                "services": svcs["stdout"][:2000], "deployments": deploys["stdout"][:2000]}

    def get_tool_schemas(self):
        return [
            {"type":"function","function":{"name":"kubectl_get","description":"Get Kubernetes resources","parameters":{"type":"object","properties":{"resource":{"type":"string","description":"e.g. pods, services, deployments, nodes"},"namespace":{"type":"string"},"output":{"type":"string","enum":["wide","json","yaml",""]}},"required":["resource"]}}},
            {"type":"function","function":{"name":"kubectl_logs","description":"Get pod logs","parameters":{"type":"object","properties":{"pod":{"type":"string"},"namespace":{"type":"string"},"tail":{"type":"integer"},"container":{"type":"string"}},"required":["pod"]}}},
            {"type":"function","function":{"name":"kubectl_describe","description":"Describe a resource","parameters":{"type":"object","properties":{"resource":{"type":"string"},"name":{"type":"string"},"namespace":{"type":"string"}},"required":["resource","name"]}}},
            {"type":"function","function":{"name":"kubectl_scale","description":"Scale a deployment","parameters":{"type":"object","properties":{"deployment":{"type":"string"},"replicas":{"type":"integer"},"namespace":{"type":"string"}},"required":["deployment","replicas"]}}},
            {"type":"function","function":{"name":"kubectl_apply","description":"Apply a manifest from stdin","parameters":{"type":"object","properties":{"manifest_yaml":{"type":"string","description":"YAML manifest content"}},"required":["manifest_yaml"]}}}
        ]

    def execute_tool_call(self, ssh, fn, args):
        ns = f"-n {args['namespace']}" if args.get("namespace") else "--all-namespaces"
        if fn == "kubectl_get":
            out = f"-o {args['output']}" if args.get("output") else ""
            return self._exec(ssh, f"kubectl get {args['resource']} {ns} {out} 2>&1")["stdout"]
        elif fn == "kubectl_logs":
            tail = f"--tail={args.get('tail',100)}"
            cont = f"-c {args['container']}" if args.get("container") else ""
            ns2 = f"-n {args.get('namespace','default')}"
            return self._exec(ssh, f"kubectl logs {args['pod']} {ns2} {tail} {cont} 2>&1", timeout=30)["stdout"]
        elif fn == "kubectl_describe":
            ns2 = f"-n {args.get('namespace','default')}"
            return self._exec(ssh, f"kubectl describe {args['resource']} {args['name']} {ns2} 2>&1")["stdout"]
        elif fn == "kubectl_scale":
            ns2 = f"-n {args.get('namespace','default')}"
            return self._exec(ssh, f"kubectl scale deployment {args['deployment']} --replicas={args['replicas']} {ns2} 2>&1")["stdout"]
        elif fn == "kubectl_apply":
            return self._exec(ssh, f"echo '{args['manifest_yaml']}' | kubectl apply -f - 2>&1")["stdout"]
        return f"Unknown: {fn}"
