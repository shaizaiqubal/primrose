import fcntl
import os
import secrets
from pathlib import Path


def get_or_create_secret(configured_secret: str | None, secret_file: Path) -> str:
    if configured_secret:
        return configured_secret

    secret_file.parent.mkdir(parents=True, exist_ok=True)
    lock_file = secret_file.with_name(f"{secret_file.name}.lock")

    with lock_file.open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            try:
                existing_secret = secret_file.read_text(encoding="utf-8").strip()
            except FileNotFoundError:
                existing_secret = ""

            if existing_secret:
                return existing_secret

            secret = secrets.token_urlsafe(64)
            descriptor = os.open(secret_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as file:
                file.write(secret)
                file.flush()
                os.fsync(file.fileno())
            return secret
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)