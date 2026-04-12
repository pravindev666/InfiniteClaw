"""InfiniteClaw — Jenkins Adapter"""
from tools.base import DevOpsToolAdapter, DetectionResult, ToolStatus, _parse_version, _check_service, _check_port, _check_binary

class JenkinsAdapter(DevOpsToolAdapter):
    name = "jenkins"
    display_name = "Jenkins"
    icon = "🔧"
    category = "ci_cd"
    default_port = 8080
    description = "CI/CD automation server"

    def detect(self, ssh) -> DetectionResult:
        svc = _check_service(ssh, "jenkins")
        if svc == "active":
            r = self._exec(ssh, "jenkins --version 2>/dev/null || java -jar /usr/share/java/jenkins.war --version 2>/dev/null")
            return DetectionResult(ToolStatus.RUNNING, _parse_version(r["stdout"]), self.default_port)
        if _check_binary(ssh, "jenkins") or _check_port(ssh, self.default_port):
            return DetectionResult(ToolStatus.STOPPED if svc == "inactive" else ToolStatus.RUNNING)
        return DetectionResult(ToolStatus.NOT_INSTALLED)

    def get_dashboard_data(self, ssh) -> dict:
        jobs = self._exec(ssh, "curl -s http://localhost:8080/api/json?tree=jobs[name,color] 2>/dev/null")
        queue = self._exec(ssh, "curl -s http://localhost:8080/queue/api/json 2>/dev/null")
        return {"jobs_raw": jobs["stdout"][:3000], "queue_raw": queue["stdout"][:1000]}

    def get_tool_schemas(self):
        return [{"type":"function","function":{"name":"jenkins_list_jobs","description":"List all Jenkins jobs","parameters":{"type":"object","properties":{}}}},
                {"type":"function","function":{"name":"jenkins_build_job","description":"Trigger a Jenkins job build","parameters":{"type":"object","properties":{"job_name":{"type":"string","description":"Name of the job"}},"required":["job_name"]}}},
                {"type":"function","function":{"name":"jenkins_job_status","description":"Get status of a Jenkins job","parameters":{"type":"object","properties":{"job_name":{"type":"string"}},"required":["job_name"]}}}]

    def execute_tool_call(self, ssh, fn, args):
        if fn == "jenkins_list_jobs":
            r = self._exec(ssh, "curl -s http://localhost:8080/api/json?tree=jobs[name,color,url] 2>/dev/null")
            return r["stdout"] or "Could not reach Jenkins API"
        elif fn == "jenkins_build_job":
            name = args["job_name"]
            r = self._exec(ssh, f"curl -s -X POST http://localhost:8080/job/{name}/build 2>/dev/null")
            return f"Build triggered for {name}" if r["exit_code"] == 0 else r["stderr"]
        elif fn == "jenkins_job_status":
            name = args["job_name"]
            r = self._exec(ssh, f"curl -s http://localhost:8080/job/{name}/lastBuild/api/json?tree=result,number,timestamp,duration 2>/dev/null")
            return r["stdout"] or "Could not get job status"
        return f"Unknown function: {fn}"
