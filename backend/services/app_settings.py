import base64
import hashlib

from cryptography.fernet import Fernet
from sqlalchemy import select

from backend.app.config import GEMINI_API_KEY, JWT_SECRET
from backend.app.database import SessionLocal
from backend.app.models import AppSetting

GEMINI_KEY = "gemini_api_key"


def _fernet() -> Fernet:
    if not JWT_SECRET:
        raise RuntimeError("JWT_SECRET is not configured")
    key = base64.urlsafe_b64encode(hashlib.sha256(JWT_SECRET.encode()).digest())
    return Fernet(key)


def get_gemini_api_key() -> str | None:
    with SessionLocal() as db:
        setting = db.get(AppSetting, GEMINI_KEY)
        if setting is None:
            return GEMINI_API_KEY
        return _fernet().decrypt(setting.encrypted_value.encode()).decode()


def save_gemini_api_key(api_key: str) -> None:
    encrypted = _fernet().encrypt(api_key.strip().encode()).decode()
    with SessionLocal.begin() as db:
        setting = db.get(AppSetting, GEMINI_KEY)
        if setting is None:
            db.add(AppSetting(key=GEMINI_KEY, encrypted_value=encrypted))
        else:
            setting.encrypted_value = encrypted


def clear_gemini_api_key() -> None:
    with SessionLocal.begin() as db:
        setting = db.get(AppSetting, GEMINI_KEY)
        if setting is not None:
            db.delete(setting)
