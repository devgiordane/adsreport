"""Fernet encryption for app secrets.

Two encryption modes:
- app_key  (no password) — used for Facebook credentials and all service secrets.
  Key is derived from the machine salt alone. Appropriate for a self-hosted tool
  where filesystem access already implies full access.
- password key           — kept for future use / admin password-change flow.

The salt lives in ~/.adsreport/.salt.
"""

from __future__ import annotations

import base64
import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from adsreport.constants import PBKDF2_ITERATIONS, SALT_FILENAME
from adsreport.core.errors import CryptoError


def _data_dir() -> Path:
    return Path(os.environ.get("ADSREPORT_DATA_DIR", Path.home() / ".adsreport"))


def load_salt() -> bytes:
    path = _data_dir() / SALT_FILENAME
    if not path.exists():
        raise CryptoError(
            "Encryption salt file is missing. Restore it from backup; existing secrets "
            "cannot be decrypted with a newly generated salt."
        )
    salt = path.read_bytes()
    if len(salt) != 32:
        raise CryptoError("Encryption salt file is corrupt; expected 32 bytes.")
    return salt


def load_or_create_salt() -> bytes:
    path = _data_dir() / SALT_FILENAME
    if path.exists():
        return load_salt()
    salt = os.urandom(32)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(salt)
    path.chmod(0o600)
    return salt


def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def _app_key() -> bytes:
    """Derive a stable encryption key from the machine salt (no password needed)."""
    salt = load_or_create_salt()
    # Use a fixed context string so the key is distinct from password-derived keys
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(b"adsreport-app-key"))


def encrypt_secret(plaintext: str) -> str:
    """Encrypt using the machine app key — no password required."""
    return Fernet(_app_key()).encrypt(plaintext.encode()).decode()


def decrypt_secret(ciphertext: str) -> str:
    """Decrypt using the machine app key — no password required."""
    try:
        return Fernet(_app_key()).decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise CryptoError("Decryption failed — salt file may have changed.") from exc


# Kept for login / password-change flows
def encrypt(plaintext: str, password: str) -> str:
    salt = load_or_create_salt()
    key = derive_key(password, salt)
    return Fernet(key).encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str, password: str) -> str:
    salt = load_salt()
    key = derive_key(password, salt)
    try:
        return Fernet(key).decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise CryptoError("Decryption failed — wrong password or corrupt data.") from exc


def re_encrypt_all(*_: str) -> None:
    """No-op — secrets now use app key, not user password. Kept for API compatibility."""
