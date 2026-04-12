"""InfiniteClaw — Docker Adapter"""
from tools.base import DevOpsToolAdapter, DetectionResult, ToolStatus, _parse_version, _check_service

class DockerAdapter(DevOpsToolAdapter):
    name = "docker"
    display_name = "Docker"
    icon = "🐳"
    category = "containers"
    default_port = 2375
    description = "Container runtime and management"

    def detect(self, ssh) -> DetectionResult:
        r = self._exec(ssh, "docker --version 2>/dev/null")
        if r["exit_code"] == 0:
            info = self._exec(ssh, "docker info --format '{{.ServerVersion}}' 2>/dev/null")
            st = ToolStatus.RUNNING if info["exit_code"] == 0 and info["stdout"].strip() else ToolStatus.STOPPED
            return DetectionResult(st, _parse_version(r["stdout"]), self.default_port)
        return DetectionResult(ToolStatus.NOT_INSTALLED)

    def get_dashboard_data(self, ssh) -> dict:
        containers = self._exec(ssh, "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}\t{{.Ports}}' 2>/dev/null")
        images = self._exec(ssh, "docker images --format 'table {{.Repository}}\t{{.Tag}}\t{{.Size}}' 2>/dev/null")
        stats = self._exec(ssh, "docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}' 2>/dev/null")
        info = self._exec(ssh, "docker info --format 'Containers: {{.Containers}} Running: {{.ContainersRunning}} Images: {{.Images}}' 2>/dev/null")
        return {"containers": containers["stdout"][:3000], "images": images["stdout"][:2000],
                "stats": stats["stdout"][:2000], "info": info["stdout"]}

    def get_tool_schemas(self):
        return [
            {"type":"function","function":{"name":"docker_ps","description":"List running Docker containers","parameters":{"type":"object","properties":{"all":{"type":"boolean","description":"Show all containers including stopped"}}}}},
            {"type":"function","function":{"name":"docker_images","description":"List Docker images","parameters":{"type":"object","properties":{}}}},
            {"type":"function","function":{"name":"docker_logs","description":"Get container logs","parameters":{"type":"object","properties":{"container":{"type":"string"},"tail":{"type":"integer","description":"Lines from end"}},"required":["container"]}}},
            {"type":"function","function":{"name":"docker_run","description":"Run a Docker container","parameters":{"type":"object","properties":{"image":{"type":"string"},"name":{"type":"string"},"ports":{"type":"string","description":"Port mapping e.g. 8080:80"},"detach":{"type":"boolean"}},"required":["image"]}}},
            {"type":"function","function":{"name":"docker_stop","description":"Stop a container","parameters":{"type":"object","properties":{"container":{"type":"string"}},"required":["container"]}}},
            {"type":"function","function":{"name":"docker_compose","description":"Run docker compose command","parameters":{"type":"object","properties":{"action":{"type":"string","enum":["up","down","ps","logs","restart"]},"file":{"type":"string","description":"Compose file path"}},"required":["action"]}}}
        ]

    def execute_tool_call(self, ssh, fn, args):
        if fn == "docker_ps":
            flag = "-a" if args.get("all") else ""
            return self._exec(ssh, f"docker ps {flag} --format 'table {{{{.Names}}}}\t{{{{.Status}}}}\t{{{{.Image}}}}\t{{{{.Ports}}}}'")["stdout"]
        elif fn == "docker_images":
            return self._exec(ssh, "docker images --format 'table {{.Repository}}\t{{.Tag}}\t{{.Size}}'")["stdout"]
        elif fn == "docker_logs":
            tail = args.get("tail", 50)
            return self._exec(ssh, f"docker logs --tail {tail} {args['container']} 2>&1")["stdout"]
        elif fn == "docker_run":
            cmd = f"docker run"
            if args.get("detach", True): cmd += " -d"
            if args.get("name"): cmd += f" --name {args['name']}"
            if args.get("ports"): cmd += f" -p {args['ports']}"
            cmd += f" {args['image']}"
            return self._exec(ssh, cmd)["stdout"]
        elif fn == "docker_stop":
            return self._exec(ssh, f"docker stop {args['container']}")["stdout"]
        elif fn == "docker_compose":
            f = f"-f {args['file']}" if args.get("file") else ""
            action = args["action"]
            if action == "up": action = "up -d"
            return self._exec(ssh, f"docker compose {f} {action} 2>&1", timeout=60)["stdout"]
        return f"Unknown: {fn}"
