"""
InfiniteClaw — Tool Router
Master router that registers all 30 DevOps tool adapters and routes AI tool calls.
"""
from typing import Dict, List, Optional
from tools.base import DevOpsToolAdapter

# ─── Import all 30 adapters ───
from tools.jenkins_adapter import JenkinsAdapter
from tools.gitlab_adapter import GitLabAdapter
from tools.argocd_adapter import ArgoCDAdapter
from tools.github_actions_adapter import GitHubActionsAdapter
from tools.docker_adapter import DockerAdapter
from tools.kubernetes_adapter import KubernetesAdapter
from tools.helm_adapter import HelmAdapter
from tools.podman_adapter import PodmanAdapter
from tools.harbor_adapter import HarborAdapter
from tools.prometheus_adapter import PrometheusAdapter
from tools.grafana_adapter import GrafanaAdapter
from tools.splunk_adapter import SplunkAdapter
from tools.elk_adapter import ELKAdapter
from tools.nagios_adapter import NagiosAdapter
from tools.jaeger_adapter import JaegerAdapter
from tools.zabbix_adapter import ZabbixAdapter
from tools.aws_adapter import AWSAdapter
from tools.ansible_adapter import AnsibleAdapter
from tools.terraform_adapter import TerraformAdapter
from tools.chef_adapter import ChefAdapter
from tools.puppet_adapter import PuppetAdapter
from tools.packer_adapter import PackerAdapter
from tools.vault_adapter import VaultAdapter
from tools.consul_adapter import ConsulAdapter
from tools.sonarqube_adapter import SonarQubeAdapter
from tools.trivy_adapter import TrivyAdapter
from tools.nginx_adapter import NginxAdapter
from tools.haproxy_adapter import HAProxyAdapter
from tools.traefik_adapter import TraefikAdapter
from tools.kafka_adapter import KafkaAdapter
from tools.rabbitmq_adapter import RabbitMQAdapter
from tools.nexus_adapter import NexusAdapter


# ─── Category Registry ───
TOOL_CATEGORIES = {
    "ci_cd": {"label": "🏗️ CI/CD", "tools": []},
    "containers": {"label": "🐳 Containers", "tools": []},
    "monitoring": {"label": "📡 Monitoring", "tools": []},
    "config_iac": {"label": "⚙️ Config & IaC", "tools": []},
    "security": {"label": "🛡️ Security", "tools": []},
    "networking": {"label": "🌐 Networking", "tools": []},
    "data": {"label": "📦 Data & Messaging", "tools": []},
}


class ToolRouter:
    """Master router for all 30 DevOps tool adapters."""

    def __init__(self):
        self.adapters: Dict[str, DevOpsToolAdapter] = {}
        self._register_all()

    def _register_all(self):
        """Register all adapters."""
        all_adapters = [
            # CI/CD
            JenkinsAdapter(), GitLabAdapter(), ArgoCDAdapter(), GitHubActionsAdapter(),
            # Containers
            DockerAdapter(), KubernetesAdapter(), HelmAdapter(), PodmanAdapter(), HarborAdapter(),
            # Monitoring
            PrometheusAdapter(), GrafanaAdapter(), SplunkAdapter(), ELKAdapter(),
            NagiosAdapter(), JaegerAdapter(), ZabbixAdapter(), AWSAdapter(),
            # Config & IaC
            AnsibleAdapter(), TerraformAdapter(), ChefAdapter(), PuppetAdapter(),
            PackerAdapter(), VaultAdapter(), ConsulAdapter(),
            # Security
            SonarQubeAdapter(), TrivyAdapter(),
            # Networking
            NginxAdapter(), HAProxyAdapter(), TraefikAdapter(),
            # Data & Messaging
            KafkaAdapter(), RabbitMQAdapter(), NexusAdapter(),
        ]

        for adapter in all_adapters:
            self.adapters[adapter.name] = adapter
            cat = adapter.category
            if cat in TOOL_CATEGORIES:
                TOOL_CATEGORIES[cat]["tools"].append(adapter.name)

    def get_adapter(self, tool_name: str) -> Optional[DevOpsToolAdapter]:
        return self.adapters.get(tool_name)

    def get_all_adapters(self) -> Dict[str, DevOpsToolAdapter]:
        return self.adapters

    def get_adapters_by_category(self, category: str) -> List[DevOpsToolAdapter]:
        tool_names = TOOL_CATEGORIES.get(category, {}).get("tools", [])
        return [self.adapters[n] for n in tool_names if n in self.adapters]

    def get_tool_schemas(self, tool_name: str = None) -> List[Dict]:
        """Get LLM function-calling schemas for one or all tools."""
        schemas = []
        # Always include the base SSH/terminal tools
        schemas.extend(self._base_tool_schemas())

        if tool_name and tool_name in self.adapters:
            schemas.extend(self.adapters[tool_name].get_tool_schemas())
        else:
            # All tool schemas (used in general chat with no specific tool context)
            for adapter in self.adapters.values():
                schemas.extend(adapter.get_tool_schemas())
        return schemas

    def execute_tool_call(self, ssh_conn, function_name: str, arguments: dict) -> str:
        """Route a tool call to the correct adapter."""
        # Check base tools first
        base_result = self._execute_base_tool(ssh_conn, function_name, arguments)
        if base_result is not None:
            return base_result

        # Route to specific adapter
        for adapter in self.adapters.values():
            schema_names = [s["function"]["name"] for s in adapter.get_tool_schemas()]
            if function_name in schema_names:
                return adapter.execute_tool_call(ssh_conn, function_name, arguments)

        return f"Unknown tool function: {function_name}"

    def _base_tool_schemas(self) -> List[Dict]:
        """Base tools available regardless of DevOps tool context."""
        return [
            {"type": "function", "function": {
                "name": "run_ssh_command",
                "description": "Execute any shell command on the connected remote server via SSH",
                "parameters": {"type": "object", "properties": {
                    "command": {"type": "string", "description": "Shell command to execute"}
                }, "required": ["command"]}
            }},
            {"type": "function", "function": {
                "name": "check_system_info",
                "description": "Get system info (OS, CPU, RAM, disk) of the connected server",
                "parameters": {"type": "object", "properties": {}}
            }},
            {"type": "function", "function": {
                "name": "check_service_status",
                "description": "Check if a systemd service is running",
                "parameters": {"type": "object", "properties": {
                    "service": {"type": "string", "description": "Service name"}
                }, "required": ["service"]}
            }},
        ]

    def _execute_base_tool(self, ssh_conn, fn: str, args: dict) -> Optional[str]:
        if fn == "run_ssh_command":
            r = ssh_conn.execute(args["command"], timeout=30)
            output = r["stdout"]
            if r["stderr"]:
                output += f"\nSTDERR: {r['stderr']}"
            output += f"\n[exit_code: {r['exit_code']}]"
            return output
        elif fn == "check_system_info":
            r = ssh_conn.execute("uname -a && echo '---' && cat /etc/os-release 2>/dev/null && echo '---' && free -h && echo '---' && df -h /")
            return r["stdout"]
        elif fn == "check_service_status":
            r = ssh_conn.execute(f"systemctl status {args['service']} 2>&1")
            return r["stdout"]
        return None


# Global singleton
tool_router = ToolRouter()
