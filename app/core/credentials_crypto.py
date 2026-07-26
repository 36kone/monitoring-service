import base64
import hashlib
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .config import settings


def _key() -> bytes:
    configured = settings.CREDENTIALS_ENCRYPTION_KEY
    if configured:
        try:
            decoded = base64.urlsafe_b64decode(configured.encode())
            if len(decoded) == 32:
                return decoded
        except ValueError:
            pass
    return hashlib.sha256((settings.SECRET_KEY or "development-key").encode()).digest()


def encrypt_credentials(value: dict) -> tuple[str, str]:
    nonce = os.urandom(12)
    encrypted = AESGCM(_key()).encrypt(nonce, _json_bytes(value), None)
    return base64.urlsafe_b64encode(encrypted).decode(), base64.urlsafe_b64encode(nonce).decode()


def decrypt_credentials(encrypted: str, nonce: str) -> dict:
    payload = AESGCM(_key()).decrypt(
        base64.urlsafe_b64decode(nonce), base64.urlsafe_b64decode(encrypted), None
    )
    import json

    return json.loads(payload)


def _json_bytes(value: dict) -> bytes:
    import json

    return json.dumps(value, separators=(",", ":")).encode()
