from datetime import datetime, timedelta, timezone
import hashlib, hmac, os
import jwt
from fastapi import HTTPException, status
from .config import settings

ALGO = "HS256"

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 260_000)
    return f"pbkdf2_sha256$260000${salt.hex()}${dk.hex()}"

def verify_password(password: str, stored: str) -> bool:
    try:
        algo, rounds, salt_hex, digest_hex = stored.split("$")
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(rounds)).hex()
        return hmac.compare_digest(candidate, digest_hex)
    except Exception:
        return False

def create_token(user_id: int) -> str:
    payload = {"sub": str(user_id), "exp": datetime.now(timezone.utc) + timedelta(hours=12)}
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGO)

def decode_token(token: str) -> int:
    try:
        p = jwt.decode(token, settings.jwt_secret, algorithms=[ALGO])
        return int(p["sub"])
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from e
