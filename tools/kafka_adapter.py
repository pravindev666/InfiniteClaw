"""InfiniteClaw — Kafka Adapter"""
from tools.base import DevOpsToolAdapter, DetectionResult, ToolStatus, _check_port

class KafkaAdapter(DevOpsToolAdapter):
    name = "kafka"; display_name = "Kafka"; icon = "📬"; category = "data"; default_port = 9092
    description = "Distributed event streaming platform"

    def detect(self, ssh) -> DetectionResult:
        if _check_port(ssh, 9092):
            return DetectionResult(ToolStatus.RUNNING, None, 9092)
        r = self._exec(ssh, "ls /opt/kafka/bin/kafka-topics.sh 2>/dev/null || which kafka-topics 2>/dev/null")
        if r["exit_code"] == 0: return DetectionResult(ToolStatus.STOPPED, None, 9092)
        return DetectionResult(ToolStatus.NOT_INSTALLED)

    def get_dashboard_data(self, ssh) -> dict:
        topics = self._exec(ssh, "/opt/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092 2>/dev/null || kafka-topics --list --bootstrap-server localhost:9092 2>/dev/null")
        return {"topics": topics["stdout"][:2000]}

    def get_tool_schemas(self):
        return [{"type":"function","function":{"name":"kafka_topics","description":"List Kafka topics","parameters":{"type":"object","properties":{}}}},
                {"type":"function","function":{"name":"kafka_consumer_groups","description":"List consumer groups","parameters":{"type":"object","properties":{}}}}]

    def execute_tool_call(self, ssh, fn, args):
        pfx = "/opt/kafka/bin/"
        if fn == "kafka_topics": return self._exec(ssh, f"{pfx}kafka-topics.sh --list --bootstrap-server localhost:9092 2>/dev/null || kafka-topics --list --bootstrap-server localhost:9092 2>/dev/null")["stdout"]
        if fn == "kafka_consumer_groups": return self._exec(ssh, f"{pfx}kafka-consumer-groups.sh --list --bootstrap-server localhost:9092 2>/dev/null || kafka-consumer-groups --list --bootstrap-server localhost:9092 2>/dev/null")["stdout"]
        return f"Unknown: {fn}"
