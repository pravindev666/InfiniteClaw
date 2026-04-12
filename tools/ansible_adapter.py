"""InfiniteClaw — Ansible Adapter"""
from tools.base import DevOpsToolAdapter, DetectionResult, ToolStatus, _parse_version, _check_binary

class AnsibleAdapter(DevOpsToolAdapter):
    name = "ansible"; display_name = "Ansible"; icon = "🤖"; category = "config_iac"; default_port = 0
    description = "Agentless IT automation and configuration management"

    def detect(self, ssh) -> DetectionResult:
        r = self._exec(ssh, "ansible --version 2>/dev/null")
        if r["exit_code"] == 0:
            return DetectionResult(ToolStatus.RUNNING, _parse_version(r["stdout"]))
        return DetectionResult(ToolStatus.NOT_INSTALLED)

    def get_dashboard_data(self, ssh) -> dict:
        inv = self._exec(ssh, "ansible-inventory --list --yaml 2>/dev/null | head -100")
        cfg = self._exec(ssh, "ansible-config dump --only-changed 2>/dev/null")
        return {"inventory": inv["stdout"][:3000], "config": cfg["stdout"][:1000]}

    def get_tool_schemas(self):
        return [{"type":"function","function":{"name":"ansible_ping","description":"Ping hosts in inventory","parameters":{"type":"object","properties":{"pattern":{"type":"string","description":"Host pattern (default: all)"}}}}},
                {"type":"function","function":{"name":"ansible_playbook","description":"Run an Ansible playbook","parameters":{"type":"object","properties":{"playbook":{"type":"string","description":"Path to playbook YAML"},"inventory":{"type":"string"},"extra_vars":{"type":"string"}},"required":["playbook"]}}},
                {"type":"function","function":{"name":"ansible_adhoc","description":"Run ad-hoc command on hosts","parameters":{"type":"object","properties":{"pattern":{"type":"string"},"module":{"type":"string"},"args":{"type":"string"}},"required":["pattern","module"]}}}]

    def execute_tool_call(self, ssh, fn, args):
        if fn == "ansible_ping":
            p = args.get("pattern", "all")
            return self._exec(ssh, f"ansible {p} -m ping 2>&1", timeout=30)["stdout"]
        elif fn == "ansible_playbook":
            inv = f"-i {args['inventory']}" if args.get("inventory") else ""
            ev = f"-e '{args['extra_vars']}'" if args.get("extra_vars") else ""
            return self._exec(ssh, f"ansible-playbook {args['playbook']} {inv} {ev} 2>&1", timeout=120)["stdout"]
        elif fn == "ansible_adhoc":
            a = f"-a '{args['args']}'" if args.get("args") else ""
            return self._exec(ssh, f"ansible {args['pattern']} -m {args['module']} {a} 2>&1", timeout=60)["stdout"]
        return f"Unknown: {fn}"
