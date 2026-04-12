"""
InfiniteClaw — DevOps Tool Base Adapter
Abstract base class that all 30 tool adapters inherit from.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from enum import Enum


class ToolStatus(Enum):
    RUNNING = "running"       # 🟢
    STOPPED = "stopped"       # 🟡
    NOT_INSTALLED = "not_installed"  # 🔴
    ERROR = "error"           # ❌
    UNKNOWN = "unknown"       # ⚪

    @property
    def icon(self) -> str:
        return {
            "running": "🟢", "stopped": "🟡",
            "not_installed": "🔴", "error": "❌", "unknown": "⚪"
        }.get(self.value, "⚪")


@dataclass
class DetectionResult:
    status: ToolStatus
    version: Optional[str] = None
    port: Optional[int] = None
    extra_info: Dict = field(default_factory=dict)


class DevOpsToolAdapter(ABC):
    """Abstract base class for all DevOps tool adapters."""

    name: str = ""               # e.g. "jenkins"
    display_name: str = ""       # e.g. "Jenkins"
    icon: str = "🔧"
    category: str = ""           # e.g. "ci_cd", "containers", "monitoring"
    default_port: int = 0
    description: str = ""

    def _exec(self, ssh_conn, command: str, timeout: int = 15) -> dict:
        """Execute a command on the remote server via SSH."""
        try:
            return ssh_conn.execute(command, timeout=timeout)
        except Exception as e:
            return {"stdout": "", "stderr": str(e), "exit_code": -1}

    @abstractmethod
    def detect(self, ssh_conn) -> DetectionResult:
        """Detect if this tool is installed and its status on the server."""
        pass

    @abstractmethod
    def get_dashboard_data(self, ssh_conn) -> dict:
        """Fetch live data for the pictorial GUI dashboard."""
        pass

    def get_tool_schemas(self) -> List[Dict]:
        """Return OpenAI function-calling schemas for this tool's commands."""
        return []

    def execute_tool_call(self, ssh_conn, function_name: str, arguments: dict) -> str:
        """Execute a tool call from the LLM."""
        return f"Tool call '{function_name}' not implemented for {self.display_name}"


def _parse_version(output: str) -> Optional[str]:
    """Helper to extract version strings from command output."""
    import re
    match = re.search(r'(\d+\.\d+[\.\d]*)', output)
    return match.group(1) if match else None


def _check_service(ssh_conn, service_name: str) -> str:
    """Check systemctl status. Returns 'active', 'inactive', or 'not_found'."""
    try:
        result = ssh_conn.execute(f"systemctl is-active {service_name} 2>/dev/null", timeout=10)
        status = result["stdout"].strip().lower()
        if status == "active":
            return "active"
        elif status in ("inactive", "failed", "deactivating"):
            return "inactive"
        return "not_found"
    except Exception:
        return "not_found"


def _check_port(ssh_conn, port: int) -> bool:
    """Check if a port is listening."""
    try:
        result = ssh_conn.execute(f"ss -tlnp 2>/dev/null | grep ':{port} ' || netstat -tlnp 2>/dev/null | grep ':{port} '", timeout=10)
        return bool(result["stdout"].strip())
    except Exception:
        return False


def _check_binary(ssh_conn, binary_name: str) -> bool:
    """Check if a binary exists on PATH."""
    try:
        result = ssh_conn.execute(f"which {binary_name} 2>/dev/null || command -v {binary_name} 2>/dev/null", timeout=10)
        return result["exit_code"] == 0 and bool(result["stdout"].strip())
    except Exception:
        return False
