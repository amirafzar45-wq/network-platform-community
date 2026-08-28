import base64, hashlib, os
from cryptography.fernet import Fernet
from app.core.config import settings

# Derive a stable Fernet key from JWT_SECRET. Replace with a dedicated key in a hardened release.
def _fernet():
    raw = hashlib.sha256(settings.jwt_secret.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(raw))

def encrypt(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()

def decrypt(value: str) -> str:
    return _fernet().decrypt(value.encode()).decode()
