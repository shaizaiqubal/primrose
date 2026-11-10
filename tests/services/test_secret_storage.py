from pathlib import Path

from backend.app.secret_storage import get_or_create_secret


def test_configured_secret_is_preserved(tmp_path: Path):
    secret_file = tmp_path / "jwt_secret"

    secret = get_or_create_secret("existing-development-secret", secret_file)

    assert secret == "existing-development-secret"
    assert not secret_file.exists()


def test_generated_secret_is_persisted_and_reused(tmp_path: Path):
    secret_file = tmp_path / "persistent" / "jwt_secret"

    first_secret = get_or_create_secret(None, secret_file)
    second_secret = get_or_create_secret(None, secret_file)

    assert first_secret
    assert second_secret == first_secret
    assert secret_file.read_text(encoding="utf-8") == first_secret