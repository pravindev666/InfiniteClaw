"""
InfiniteClaw — Configuration Manager
Local-only config with encrypted vault for API keys.
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ─── Paths ───
INFINITECLAW_HOME = Path(os.path.expanduser("~")) / ".infiniteclaw"
INFINITECLAW_HOME.mkdir(parents=True, exist_ok=True)
DB_PATH = INFINITECLAW_HOME / "infiniteclaw.db"
VAULT_PATH = INFINITECLAW_HOME / "vault.enc"
METRICS_DIR = INFINITECLAW_HOME / "metrics"
METRICS_DIR.mkdir(parents=True, exist_ok=True)
SOUL_PATH = Path(__file__).parent.parent / "SOUL.md"

# ─── Environment ───
ENVIRONMENT = os.getenv("INFINITECLAW_ENVIRONMENT", "desktop")

# ─── LLM Provider Key Map ───
PROVIDER_KEY_MAP = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "nvidia": "NVIDIA_API_KEY",
    "google": "GOOGLE_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
}

PROVIDER_ENV_MAP = {
    "openai": "openai_key",
    "anthropic": "anthropic_key",
    "nvidia": "nvidia_key",
    "google": "google_key",
    "deepseek": "deepseek_key",
}


def get_key(provider: str) -> str:
    """Get API key for a provider. Checks env vars first, then local DB."""
    env_var = PROVIDER_KEY_MAP.get(provider, f"{provider.upper()}_API_KEY")
    env_val = os.getenv(env_var, "")
    if env_val:
        return env_val

    # Fallback to local DB
    try:
        from core.local_db import get_key_local, get_current_user_id
        user_id = get_current_user_id()
        if user_id:
            col = PROVIDER_ENV_MAP.get(provider, f"{provider}_key")
            return get_key_local(user_id, col)
    except Exception:
        pass
    return ""


def set_key(provider: str, key: str):
    """Store API key in local DB vault."""
    from core.local_db import set_key_local, get_current_user_id
    user_id = get_current_user_id()
    if user_id:
        col = PROVIDER_ENV_MAP.get(provider, f"{provider}_key")
        set_key_local(user_id, col, key)


def get_all_keys() -> dict:
    """Return dict of {provider: bool} indicating which keys are configured."""
    keys = {}
    for provider in PROVIDER_KEY_MAP:
        val = get_key(provider)
        if val:
            keys[provider] = True
    return keys


def get_soul() -> str:
    """Load the SOUL.md personality directive."""
    if SOUL_PATH.exists():
        return SOUL_PATH.read_text(encoding="utf-8")
    return "You are InfiniteClaw, a DevOps AI infrastructure manager."


# ─── Model Catalog ───
AVAILABLE_MODELS = [
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
    "openai/gpt-4-turbo",
    "openai/gpt-3.5-turbo",
    "anthropic/claude-3-5-sonnet-20241022",
    "anthropic/claude-3-haiku-20240307",
    "nvidia/meta-llama-3-70b-instruct",
    "google/gemini-1.5-pro",
    "google/gemini-1.5-flash",
    "deepseek/deepseek-chat",
]

DEFAULT_MODEL = "openai/gpt-4o-mini"
