import pytest

from backend.services import app_settings


def test_get_gemini_api_key_raises_when_database_setting_is_missing(monkeypatch):
    class EmptySession:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def get(self, model, key):
            return None

    monkeypatch.setattr(app_settings, "SessionLocal", EmptySession)

    with pytest.raises(RuntimeError, match="Gemini API key is not configured"):
        app_settings.get_gemini_api_key()