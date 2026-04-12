"""
InfiniteClaw — Encrypted Vault
PBKDF2-encrypted local vault for API keys and SSH credentials.
"""
import os
import json
import base64
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from core.config import VAULT_PATH

_SALT = b"InfiniteClaw_v1_salt_2024"


def _derive_key(passphrase: str) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_SALT,
        iterations=480000,
    )
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))


def encrypt_data(data: dict, passphrase: str) -> bytes:
    key = _derive_key(passphrase)
    f = Fernet(key)
    return f.encrypt(json.dumps(data).encode())


def decrypt_data(encrypted: bytes, passphrase: str) -> dict:
    key = _derive_key(passphrase)
    f = Fernet(key)
    return json.loads(f.decrypt(encrypted).decode())


def save_vault(data: dict, passphrase: str = "infiniteclaw"):
    encrypted = encrypt_data(data, passphrase)
    VAULT_PATH.write_bytes(encrypted)


def load_vault(passphrase: str = "infiniteclaw") -> dict:
    if not VAULT_PATH.exists():
        return {}
    try:
        return decrypt_data(VAULT_PATH.read_bytes(), passphrase)
    except Exception:
        return {}


def encrypt_key(provider: str, key: str, passphrase: str = "infiniteclaw"):
    vault = load_vault(passphrase)
    vault[provider] = key
    save_vault(vault, passphrase)


def decrypt_key(provider: str, passphrase: str = "infiniteclaw") -> str:
    vault = load_vault(passphrase)
    return vault.get(provider, "")
