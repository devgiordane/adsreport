from __future__ import annotations

import pytest

from adsreport.core.crypto import decrypt, encrypt
from adsreport.core.errors import CryptoError


def test_encrypt_decrypt_roundtrip():
    password = "hunter2correct"
    plaintext = "super-secret-token-EAAB1234567890"
    ciphertext = encrypt(plaintext, password)
    assert ciphertext != plaintext
    assert decrypt(ciphertext, password) == plaintext


def test_wrong_password_raises():
    password = "correct-password"
    ciphertext = encrypt("secret", password)
    with pytest.raises(CryptoError):
        decrypt(ciphertext, "wrong-password")


def test_different_plaintexts_produce_different_ciphertexts():
    password = "same-password"
    ct1 = encrypt("value_a", password)
    ct2 = encrypt("value_b", password)
    assert ct1 != ct2


def test_same_plaintext_same_password_produces_different_ciphertexts():
    # Fernet uses a random IV — same input should not produce deterministic output
    password = "pw"
    ct1 = encrypt("secret", password)
    ct2 = encrypt("secret", password)
    assert ct1 != ct2
    assert decrypt(ct1, password) == decrypt(ct2, password) == "secret"
