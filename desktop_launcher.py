"""
InfiniteClaw — Desktop Launcher
Starts the Streamlit backend and opens a native window via PyWebView.
Usage: python desktop_launcher.py
"""
import sys
import os
import time
import signal
import subprocess
import threading
import socket

# Fix Windows terminal encoding for Unicode
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

STREAMLIT_PORT = 8501
STREAMLIT_HOST = "localhost"


def find_free_port(start=9600, end=9699):
    """Find a free port in range."""
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("", port))
                return port
            except OSError:
                continue
    return start


def start_streamlit(port: int):
    """Start Streamlit server as a subprocess."""
    app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")
    cmd = [
        sys.executable, "-m", "streamlit", "run", app_path,
        "--server.port", str(port),
        "--server.address", STREAMLIT_HOST,
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
        "--theme.base", "dark",
        "--theme.primaryColor", "#00f0ff",
        "--theme.backgroundColor", "#0a0e17",
        "--theme.secondaryBackgroundColor", "#111827",
        "--theme.textColor", "#f1f5f9",
    ]

    env = os.environ.copy()
    env["INFINITECLAW_ENVIRONMENT"] = "desktop"

    process = subprocess.Popen(
        cmd, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    return process


def wait_for_server(port: int, timeout: int = 30):
    """Wait until the Streamlit server is ready."""
    import urllib.request
    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(f"http://{STREAMLIT_HOST}:{port}/_stcore/health")
            return True
        except Exception:
            time.sleep(0.5)
    return False


def open_native_window(port: int):
    """Open a native desktop window using PyWebView."""
    try:
        import webview
        window = webview.create_window(
            title="∞ InfiniteClaw — DevOps AI Command Center",
            url=f"http://{STREAMLIT_HOST}:{port}",
            width=1400,
            height=900,
            resizable=True,
            min_size=(1000, 600),
        )
        webview.start()
    except ImportError:
        print("PyWebView not installed. Opening in browser...")
        import webbrowser
        webbrowser.open(f"http://{STREAMLIT_HOST}:{port}")
        # Keep alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass


def main():
    print("""
    ╔══════════════════════════════════════════╗
    ║    ∞  I N F I N I T E C L A W           ║
    ║    Desktop Launcher                       ║
    ║    Starting backend...                    ║
    ╚══════════════════════════════════════════╝
    """)

    port = find_free_port()
    print(f"[InfiniteClaw] Starting on port {port}...")

    # Start Streamlit
    process = start_streamlit(port)

    # Wait for server
    print("[InfiniteClaw] Waiting for server to be ready...")
    if wait_for_server(port):
        print(f"[InfiniteClaw] Server ready at http://{STREAMLIT_HOST}:{port}")
    else:
        print("[InfiniteClaw] WARNING: Server may not be ready yet")

    # Open window
    try:
        open_native_window(port)
    finally:
        print("[InfiniteClaw] Shutting down...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        print("[InfiniteClaw] Goodbye! ∞")


if __name__ == "__main__":
    main()
