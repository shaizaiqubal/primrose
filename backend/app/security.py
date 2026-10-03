from pwdlib import PasswordHash
import hashlib
import secrets

password_hash = PasswordHash.recommended()

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(password: str, hashed_password: str)-> bool:
    return password_hash.verify(password, hashed_password)


def generate_verification_token() -> str:
    return secrets.token_urlsafe(32)

def hash_verification_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

import jwt
from datetime import datetime, timedelta, timezone
from backend.app.config import JWT_SECRET

if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET is not set")

ACCESS_TOKEN_EXPIRE_MINUTES = 15

def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "access",
    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm="HS256",
    )

def create_refresh_token() -> str:
    return secrets.token_urlsafe(32)

