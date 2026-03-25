"""Encryption utilities using Fernet symmetric encryption."""

import base64
import hashlib
from cryptography.fernet import Fernet
from flask import current_app


import os

def _get_fernet():
    """Get Fernet instance using the ENCRYPTION_KEY from environment."""
    key = os.environ.get("ENCRYPTION_KEY")
    if not key:
        raise ValueError("ENCRYPTION_KEY is required in .env file")
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_value(plain_text):
    """Encrypt a plaintext string. Returns a base64-encoded encrypted string."""
    if not plain_text:
        return ''
    f = _get_fernet()
    return f.encrypt(plain_text.encode()).decode()


def decrypt_value(encrypted_text):
    """Decrypt an encrypted string. Returns the original plaintext."""
    if not encrypted_text:
        return ''
    f = _get_fernet()
    return f.decrypt(encrypted_text.encode()).decode()
