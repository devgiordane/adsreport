"""Fernet encryption with PBKDF2-HMAC-SHA256 key derivation.

The salt is stored in ~/.adsreport/.salt (separate from the DB so that
rotating the password only requires re-deriving the key, not re-generating salt).
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


def re_encrypt_all(old_password: str, new_password: str) -> None:
    """Re-encrypt every secret in app_settings after a password change."""
    from adsreport.repositories.settings_repo import SettingsRepository

    repo = SettingsRepository()
    secrets = repo.get_all_secrets()
    for setting in secrets:
        if setting.value_encrypted:
            plaintext = decrypt(setting.value_encrypted, old_password)
            setting.value_encrypted = encrypt(plaintext, new_password)
    repo.bulk_save(secrets)
