"""
InfiniteClaw — Telegram Worker
Remote control your infrastructure via Telegram.
"""
import os
import sys
import asyncio
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from core.local_db import init_db, get_servers, get_server_tools
from core.local_db import set_current_user_id, set_current_workspace_id, get_or_create_workspace
from core.llm_engine import engine
from core.ssh_manager import ssh_manager
from tools.tool_router import tool_router
from tools.scanner import scan_server

logger = logging.getLogger(__name__)

# ─── State ───
_user_messages = {}


def _init_context():
    """Initialize DB and user context."""
    init_db()
    import sqlite3
    from core.config import DB_PATH
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


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message."""
    await update.message.reply_text(
        "∞ *InfiniteClaw* — DevOps AI Command Center\n\n"
        "Commands:\n"
        "/status — Infrastructure health\n"
        "/servers — List servers\n"
        "/scan <server> — Scan for tools\n"
        "Or just send a message to chat with AI!",
        parse_mode="Markdown"
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show infrastructure status."""
    from core.local_db import get_current_workspace_id
    ws_id = get_current_workspace_id()
    servers = get_servers(ws_id) if ws_id else []

    if not servers:
        await update.message.reply_text("⚠️ No servers connected.")
        return

    msg = "📊 *Infrastructure Status*\n\n"
    for srv in servers:
        tools = get_server_tools(srv["id"])
        running = len([t for t in tools if t["status"] == "running"])
        total = len([t for t in tools if t["status"] in ("running", "stopped")])
        msg += f"🖥️ *{srv['name']}* — `{srv['host']}`\n"
        msg += f"   🟢 {running}/{total} tools running\n\n"

    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_servers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List connected servers."""
    from core.local_db import get_current_workspace_id
    ws_id = get_current_workspace_id()
    servers = get_servers(ws_id) if ws_id else []

    if not servers:
        await update.message.reply_text("No servers connected.")
        return

    msg = "🌐 *Connected Servers*\n\n"
    for srv in servers:
        msg += f"• *{srv['name']}* — `{srv['host']}:{srv.get('port', 22)}`\n"
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Scan a server for tools."""
    from core.local_db import get_current_workspace_id
    ws_id = get_current_workspace_id()
    servers = get_servers(ws_id) if ws_id else []

    args = context.args
    if not args:
        await update.message.reply_text("Usage: /scan <server_name>")
        return

    target_name = " ".join(args)
    target = None
    for s in servers:
        if s["name"].lower() == target_name.lower() or s["host"] == target_name:
            target = s
            break

    if not target:
        await update.message.reply_text(f"❌ Server '{target_name}' not found.")
        return

    await update.message.reply_text(f"🔍 Scanning {target['name']}...")

    try:
        results = scan_server(target["id"])
        installed = [r for r in results if r["status"] not in ("not_installed", "error")]

        msg = f"✅ *Scan Results — {target['name']}*\n\n"
        for r in installed:
            icon = {"running": "🟢", "stopped": "🟡"}.get(r["status"], "⚪")
            version = f" v{r['version']}" if r.get("version") else ""
            msg += f"{icon} {r['display_name']}{version}\n"
        msg += f"\n*{len(installed)}/30* tools detected."
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Scan failed: {e}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular messages — route to AI engine."""
    user_id = str(update.effective_user.id)
    text = update.message.text

    if user_id not in _user_messages:
        _user_messages[user_id] = []

    _user_messages[user_id].append({"role": "user", "content": text})

    # Keep last 20 messages
    _user_messages[user_id] = _user_messages[user_id][-20:]

    try:
        response = engine.chat(
            messages=_user_messages[user_id],
            tool_context="Telegram Remote Control"
        )
        _user_messages[user_id].append({"role": "assistant", "content": response})

        # Split long messages for Telegram's 4096 char limit
        for i in range(0, len(response), 4000):
            await update.message.reply_text(response[i:i+4000])
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


def start_telegram_bot():
    """Start the Telegram bot."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print("[Telegram] No TELEGRAM_BOT_TOKEN set. Skipping.")
        return

    _init_context()

    print("[Telegram] Starting InfiniteClaw Telegram bot...")
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("servers", cmd_servers))
    app.add_handler(CommandHandler("scan", cmd_scan))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()


if __name__ == "__main__":
    start_telegram_bot()
