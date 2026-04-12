"""InfiniteClaw — ELK Stack Adapter (Elasticsearch + Logstash + Kibana)"""
from tools.base import DevOpsToolAdapter, DetectionResult, ToolStatus, _parse_version, _check_service, _check_port

class ELKAdapter(DevOpsToolAdapter):
    name = "elk"; display_name = "ELK Stack"; icon = "📚"; category = "monitoring"; default_port = 9200
    description = "Elasticsearch, Logstash, Kibana stack"

    def detect(self, ssh) -> DetectionResult:
        es = self._exec(ssh, "curl -s http://localhost:9200 2>/dev/null")
        if es["exit_code"] == 0 and "cluster_name" in es["stdout"]:
            version = _parse_version(es["stdout"])
            kibana = _check_port(ssh, 5601)
            logstash = _check_service(ssh, "logstash")
            return DetectionResult(ToolStatus.RUNNING, version, 9200, {"kibana": kibana, "logstash": logstash == "active"})
        if _check_service(ssh, "elasticsearch") != "not_found":
            return DetectionResult(ToolStatus.STOPPED, None, 9200)
        return DetectionResult(ToolStatus.NOT_INSTALLED)

    def get_dashboard_data(self, ssh) -> dict:
        health = self._exec(ssh, "curl -s http://localhost:9200/_cluster/health 2>/dev/null")
        indices = self._exec(ssh, "curl -s http://localhost:9200/_cat/indices?v 2>/dev/null")
        return {"cluster_health": health["stdout"][:1000], "indices": indices["stdout"][:3000]}

    def get_tool_schemas(self):
        return [{"type":"function","function":{"name":"elk_cluster_health","description":"Get Elasticsearch cluster health","parameters":{"type":"object","properties":{}}}},
                {"type":"function","function":{"name":"elk_search","description":"Search Elasticsearch index","parameters":{"type":"object","properties":{"index":{"type":"string"},"query":{"type":"string","description":"JSON query body"}},"required":["index","query"]}}},
                {"type":"function","function":{"name":"elk_indices","description":"List all indices","parameters":{"type":"object","properties":{}}}}]

    def execute_tool_call(self, ssh, fn, args):
        if fn == "elk_cluster_health":
            return self._exec(ssh, "curl -s http://localhost:9200/_cluster/health?pretty 2>/dev/null")["stdout"]
        elif fn == "elk_search":
            return self._exec(ssh, f"curl -s http://localhost:9200/{args['index']}/_search -H 'Content-Type: application/json' -d '{args['query']}' 2>/dev/null")["stdout"]
        elif fn == "elk_indices":
            return self._exec(ssh, "curl -s http://localhost:9200/_cat/indices?v 2>/dev/null")["stdout"]
        return f"Unknown: {fn}"
