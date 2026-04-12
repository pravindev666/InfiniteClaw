"""InfiniteClaw — RabbitMQ Adapter"""
from tools.base import DevOpsToolAdapter, DetectionResult, ToolStatus, _parse_version, _check_service, _check_port

class RabbitMQAdapter(DevOpsToolAdapter):
    name = "rabbitmq"; display_name = "RabbitMQ"; icon = "🐰"; category = "data"; default_port = 15672
    description = "Message broker"

    def detect(self, ssh) -> DetectionResult:
        svc = _check_service(ssh, "rabbitmq-server")
        if svc == "active":
            r = self._exec(ssh, "rabbitmqctl version 2>/dev/null")
            return DetectionResult(ToolStatus.RUNNING, _parse_version(r["stdout"]), 15672)
        if svc == "inactive": return DetectionResult(ToolStatus.STOPPED, None, 15672)
        if _check_port(ssh, 15672): return DetectionResult(ToolStatus.RUNNING, None, 15672)
        return DetectionResult(ToolStatus.NOT_INSTALLED)

    def get_dashboard_data(self, ssh) -> dict:
        queues = self._exec(ssh, "rabbitmqctl list_queues name messages consumers 2>/dev/null")
        status = self._exec(ssh, "rabbitmqctl status 2>/dev/null | head -30")
        return {"queues": queues["stdout"][:2000], "status": status["stdout"][:2000]}

    def get_tool_schemas(self):
        return [{"type":"function","function":{"name":"rabbitmq_queues","description":"List RabbitMQ queues","parameters":{"type":"object","properties":{}}}},
                {"type":"function","function":{"name":"rabbitmq_status","description":"Get RabbitMQ status","parameters":{"type":"object","properties":{}}}}]

    def execute_tool_call(self, ssh, fn, args):
        if fn == "rabbitmq_queues": return self._exec(ssh, "rabbitmqctl list_queues name messages consumers 2>&1")["stdout"]
        if fn == "rabbitmq_status": return self._exec(ssh, "rabbitmqctl status 2>&1 | head -40")["stdout"]
        return f"Unknown: {fn}"
