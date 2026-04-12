"""
InfiniteClaw — SSH Manager
Multi-server SSH connection pooling with Paramiko.
"""
import paramiko
import io
import threading
from typing import Optional, Dict
from core.local_db import get_server


class SSHConnection:
    """Wraps a Paramiko SSH client for a single server."""

    def __init__(self, server_config: dict):
        self.config = server_config
        self.client: Optional[paramiko.SSHClient] = None
        self._lock = threading.Lock()

    def connect(self) -> bool:
        with self._lock:
            try:
                self.client = paramiko.SSHClient()
                self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                connect_kwargs = {
                    "hostname": self.config["host"],
                    "port": self.config.get("port", 22),
                    "username": self.config["username"],
                    "timeout": 15,
                }

                auth = self.config.get("auth_method", "password")
                if auth == "key" and self.config.get("key_content"):
                    k_cont = self.config["key_content"]
                    if "PuTTY-User-Key-File" in k_cont:
                        raise ValueError("PuTTY (PPK) key detected. InfiniteClaw's Alpha-Mode engine requires OpenSSH (PEM) format. Please export as OpenSSH in PuTTYGen (just like in WolfClaw legacy setups).")
                    
                    key_file = io.StringIO(k_cont)
                    try:
                        pkey = paramiko.RSAKey.from_private_key(key_file)
                    except paramiko.ssh_exception.SSHException:
                        key_file.seek(0)
                        try:
                            pkey = paramiko.Ed25519Key.from_private_key(key_file)
                        except Exception:
                            key_file.seek(0)
                            pkey = paramiko.ECDSAKey.from_private_key(key_file)
                    connect_kwargs["pkey"] = pkey
                elif auth == "key" and self.config.get("key_path"):
                    connect_kwargs["key_filename"] = self.config["key_path"]
                else:
                    connect_kwargs["password"] = self.config.get("password", "")

                self.client.connect(**connect_kwargs)
                return True
            except Exception as e:
                self.client = None
                raise ConnectionError(f"SSH connection failed to {self.config['host']}: {e}")

    @property
    def is_connected(self) -> bool:
        return self.client is not None and self.client.get_transport() is not None and self.client.get_transport().is_active()

    def execute(self, command: str, timeout: int = 30) -> dict:
        """Execute a command and return {stdout, stderr, exit_code}."""
        if not self.is_connected:
            self.connect()

        with self._lock:
            stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)
            exit_code = stdout.channel.recv_exit_status()
            return {
                "stdout": stdout.read().decode("utf-8", errors="replace").strip(),
                "stderr": stderr.read().decode("utf-8", errors="replace").strip(),
                "exit_code": exit_code,
            }

    def close(self):
        with self._lock:
            if self.client:
                try:
                    self.client.close()
                except Exception:
                    pass
                self.client = None


class SSHManager:
    """Manages SSH connections to multiple servers with connection pooling."""

    def __init__(self):
        self._pool: Dict[str, SSHConnection] = {}
        self._lock = threading.Lock()

    def get_connection(self, server_id: str) -> SSHConnection:
        """Get or create an SSH connection for a server."""
        with self._lock:
            if server_id in self._pool and self._pool[server_id].is_connected:
                return self._pool[server_id]

            server = get_server(server_id)
            if not server:
                raise ValueError(f"Server {server_id} not found in database")

            conn = SSHConnection(server)
            conn.connect()
            self._pool[server_id] = conn
            return conn

    def execute_on_server(self, server_id: str, command: str, timeout: int = 30) -> dict:
        """Execute a command on a specific server."""
        conn = self.get_connection(server_id)
        return conn.execute(command, timeout)

    def test_connection(self, server_id: str) -> dict:
        """Test SSH connection to a server."""
        try:
            conn = self.get_connection(server_id)
            result = conn.execute("echo 'InfiniteClaw connected successfully'")
            return {"success": True, "message": result["stdout"]}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def close_connection(self, server_id: str):
        """Close a specific server connection."""
        with self._lock:
            if server_id in self._pool:
                self._pool[server_id].close()
                del self._pool[server_id]

    def close_all(self):
        """Close all connections."""
        with self._lock:
            for conn in self._pool.values():
                conn.close()
            self._pool.clear()


# Global singleton
ssh_manager = SSHManager()
