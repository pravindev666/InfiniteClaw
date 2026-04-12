"""
InfiniteClaw — CLI Interface
Typer-based command-line tool for managing InfiniteClaw from the terminal.
Usage: python cli.py [COMMAND]
"""
import sys
import os

# Fix Windows terminal encoding for Unicode/emoji
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich import print as rprint
from typing import Optional

app = typer.Typer(
    name="infiniteclaw",
    help="InfiniteClaw -- DevOps AI Command Center",
    add_completion=False,
)
console = Console(force_terminal=True)

BANNER = """
[bold cyan]
    +==========================================+
    |    INF  I N F I N I T E C L A W          |
    |    DevOps AI Command Center              |
    |    One Claw To Rule Them All.            |
    +==========================================+
[/bold cyan]
"""


@app.command()
def setup():
    """🔧 First-time setup wizard — configure API keys and first server."""
    from core.local_db import init_db, create_user, get_or_create_workspace, set_current_user_id, set_current_workspace_id
    import hashlib

    console.print(BANNER)
    console.print("[bold green]Welcome to InfiniteClaw Setup![/bold green]\n")

    init_db()

    # Create local user
    email = Prompt.ask("📧 Enter your email")
    password = Prompt.ask("🔒 Create a password", password=True)
    try:
        uid = create_user(email, hashlib.sha256(password.encode()).hexdigest())
        ws_id = get_or_create_workspace(uid)
        set_current_user_id(uid)
        set_current_workspace_id(ws_id)
        console.print(f"[green]✅ Account created![/green]")
    except ValueError:
        console.print("[yellow]Account already exists, logging in...[/yellow]")
        from core.local_db import get_user_by_email
        user = get_user_by_email(email)
        if user:
            set_current_user_id(user["id"])
            ws_id = get_or_create_workspace(user["id"])
            set_current_workspace_id(ws_id)

    # API Key
    console.print("\n[bold]🔑 API Key Configuration[/bold]")
    openai_key = Prompt.ask("OpenAI API Key (sk-...)", password=True, default="")
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key
        from core.config import set_key
        set_key("openai", openai_key)
        console.print("[green]✅ OpenAI key saved![/green]")

    # Server
    if Confirm.ask("\n🌐 Add a remote server now?", default=False):
        _add_server_interactive()

    console.print("\n[bold green]∞ Setup complete![/bold green]")
    console.print("Run [bold cyan]python app.py[/bold cyan] for the Streamlit UI")
    console.print("Run [bold cyan]python cli.py chat[/bold cyan] for terminal AI chat")


@app.command()
def status():
    """📊 Show infrastructure health status."""
    from core.local_db import init_db, get_servers, get_server_tools, get_usage_summary
    from core.local_db import set_current_user_id, set_current_workspace_id, get_user_by_email, get_or_create_workspace

    init_db()
    console.print(BANNER)

    # Try to get first user
    import sqlite3
    from core.config import DB_PATH
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM users LIMIT 1").fetchone()
    conn.close()

    if not row:
        console.print("[yellow]No user found. Run 'python cli.py setup' first.[/yellow]")
        return

    set_current_user_id(row["id"])
    ws_id = get_or_create_workspace(row["id"])
    set_current_workspace_id(ws_id)

    servers = get_servers(ws_id)

    if not servers:
        console.print("[yellow]No servers connected. Run 'python cli.py server add'.[/yellow]")
        return

    for srv in servers:
        console.print(f"\n[bold cyan]🖥️ {srv['name']}[/bold cyan] — {srv['host']}:{srv.get('port', 22)}")
        tools = get_server_tools(srv["id"])
        if tools:
            table = Table(title="", show_header=True)
            table.add_column("Status", justify="center", width=8)
            table.add_column("Tool", width=20)
            table.add_column("Version", width=12)
            table.add_column("Port", width=8)

            for t in tools:
                if t["status"] == "not_installed":
                    continue
                icon = {"running": "🟢", "stopped": "🟡", "error": "❌"}.get(t["status"], "⚪")
                table.add_row(icon, t["tool_name"], t.get("version", "—"), str(t.get("port", "—")))
            console.print(table)
        else:
            console.print("  [dim]No tools detected. Run scan.[/dim]")


@app.command()
def chat(model: str = typer.Option("openai/gpt-4o-mini", help="LLM model to use")):
    """💬 Interactive AI chat in terminal."""
    from core.local_db import init_db
    init_db()
    _init_session()

    console.print(BANNER)
    console.print("[bold]💬 InfiniteClaw Terminal Chat[/bold]")
    console.print("[dim]Type 'exit' or 'quit' to leave. Type '/servers' to list servers.[/dim]\n")

    from core.llm_engine import engine
    messages = []

    while True:
        try:
            user_input = Prompt.ask("[bold cyan]You[/bold cyan]")
        except (KeyboardInterrupt, EOFError):
            break

        if user_input.lower() in ("exit", "quit", "q"):
            console.print("[dim]Goodbye! ∞[/dim]")
            break

        if user_input.startswith("/servers"):
            status()
            continue

        messages.append({"role": "user", "content": user_input})

        with console.status("[cyan]Thinking...[/cyan]"):
            response = engine.chat(messages=messages, model=model)

        messages.append({"role": "assistant", "content": response})
        console.print(f"\n[bold magenta]∞ InfiniteClaw:[/bold magenta] {response}\n")


@app.command()
def scan(server_name: str = typer.Argument(..., help="Server name to scan")):
    """🔍 Scan a server for DevOps tools."""
    from core.local_db import init_db, get_servers
    init_db()
    _init_session()

    from core.local_db import get_current_workspace_id
    ws_id = get_current_workspace_id()
    servers = get_servers(ws_id) if ws_id else []

    target = None
    for s in servers:
        if s["name"].lower() == server_name.lower() or s["host"] == server_name:
            target = s
            break

    if not target:
        console.print(f"[red]Server '{server_name}' not found.[/red]")
        return

    console.print(f"[cyan]🔍 Scanning {target['name']} ({target['host']})...[/cyan]")

    from tools.scanner import scan_server
    results = scan_server(target["id"])

    table = Table(title=f"Scan Results — {target['name']}")
    table.add_column("Status", justify="center", width=8)
    table.add_column("Category", width=15)
    table.add_column("Tool", width=20)
    table.add_column("Version", width=12)
    table.add_column("Port", width=8)

    for r in results:
        if r["status"] == "not_installed":
            continue
        icon = {"running": "🟢", "stopped": "🟡", "error": "❌"}.get(r["status"], "⚪")
        table.add_row(icon, r["category"], r["display_name"], r.get("version", "—"), str(r.get("port", "—")))

    console.print(table)

    installed = [r for r in results if r["status"] not in ("not_installed", "error")]
    console.print(f"\n[green]Found {len(installed)} tools out of 30 checked.[/green]")


@app.command("server")
def server_cmd(action: str = typer.Argument("list", help="add/list/remove")):
    """🌐 Manage remote servers."""
    from core.local_db import init_db, get_servers
    init_db()
    _init_session()

    if action == "add":
        _add_server_interactive()
    elif action == "list":
        from core.local_db import get_current_workspace_id
        ws_id = get_current_workspace_id()
        servers = get_servers(ws_id) if ws_id else []
        if not servers:
            console.print("[yellow]No servers. Run 'python cli.py server add'.[/yellow]")
            return
        table = Table(title="Connected Servers")
        table.add_column("Name", width=20)
        table.add_column("Host", width=25)
        table.add_column("Port", width=8)
        table.add_column("User", width=15)
        for s in servers:
            table.add_row(s["name"], s["host"], str(s.get("port", 22)), s["username"])
        console.print(table)
    elif action == "remove":
        console.print("[yellow]Use the Streamlit UI to remove servers.[/yellow]")


def _add_server_interactive():
    """Interactive server add flow."""
    from core.local_db import add_server, get_current_workspace_id
    from core.ssh_manager import ssh_manager
    from tools.scanner import scan_server

    ws_id = get_current_workspace_id()
    if not ws_id:
        console.print("[red]No workspace. Run setup first.[/red]")
        return

    name = Prompt.ask("Server name", default="my-server")
    host = Prompt.ask("Host / IP")
    port = int(Prompt.ask("SSH port", default="22"))
    username = Prompt.ask("Username", default="ubuntu")
    auth = Prompt.ask("Auth method", choices=["password", "key"], default="password")

    password = None
    key_content = None
    if auth == "password":
        password = Prompt.ask("Password", password=True)
    else:
        key_path = Prompt.ask("Path to PEM key")
        try:
            with open(key_path, "r") as f:
                key_content = f.read()
        except Exception as e:
            console.print(f"[red]Cannot read key: {e}[/red]")
            return

    server_id = add_server(ws_id, name, host, port, username, auth, password, key_content)

    with console.status("[cyan]Testing connection...[/cyan]"):
        test = ssh_manager.test_connection(server_id)

    if test["success"]:
        console.print("[green]✅ Connected successfully![/green]")
        if Confirm.ask("Run tool scan now?", default=True):
            with console.status("[cyan]Scanning for DevOps tools...[/cyan]"):
                results = scan_server(server_id)
            installed = [r for r in results if r["status"] not in ("not_installed", "error")]
            console.print(f"[green]Found {len(installed)} tools![/green]")
    else:
        console.print(f"[red]Connection failed: {test['message']}[/red]")
        from core.local_db import delete_server
        delete_server(server_id)


def _init_session():
    """Initialize session for CLI context."""
    import sqlite3
    from core.config import DB_PATH
    from core.local_db import set_current_user_id, set_current_workspace_id, get_or_create_workspace

    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM users LIMIT 1").fetchone()
        conn.close()
        if row:
            set_current_user_id(row["id"])
            ws_id = get_or_create_workspace(row["id"])
            set_current_workspace_id(ws_id)
    except Exception:
        pass


if __name__ == "__main__":
    app()
