"""Shared safeguards for calls to the Gemini API."""

import logging
import os
import random
import time
from collections.abc import Callable
from typing import TypeVar

from google import genai
from google.genai.types import HttpOptions, HttpRetryOptions
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError

from backend.services.embedding_queue import get_redis

logger = logging.getLogger(__name__)

T = TypeVar("T")
MAX_ATTEMPTS = int(os.getenv("GEMINI_MAX_ATTEMPTS", "5"))
BASE_DELAY_SECONDS = float(os.getenv("GEMINI_RETRY_BASE_SECONDS", "2"))
MAX_DELAY_SECONDS = float(os.getenv("GEMINI_RETRY_MAX_SECONDS", "60"))
LOCK_TIMEOUT_SECONDS = int(os.getenv("GEMINI_REQUEST_LOCK_TIMEOUT_SECONDS", "180"))
LOCK_WAIT_SECONDS = int(os.getenv("GEMINI_REQUEST_LOCK_WAIT_SECONDS", "30"))
LOCK_NAME = os.getenv("GEMINI_REQUEST_LOCK_NAME", "gemini:request")
REQUEST_TIMEOUT_MS = int(os.getenv("GEMINI_REQUEST_TIMEOUT_MS", "120000"))


def create_gemini_client(api_key: str):
    """Create a client with bounded SDK retries; our wrapper owns retry timing."""
    return genai.Client(
        api_key=api_key,
        http_options=HttpOptions(
            timeout=REQUEST_TIMEOUT_MS,
            retry_options=HttpRetryOptions(attempts=1),
        ),
    )


def _status_code(error: Exception) -> int | None:
    for candidate in (
        getattr(error, "status_code", None),
        getattr(error, "code", None),
        getattr(getattr(error, "response", None), "status_code", None),
    ):
        try:
            if candidate is not None:
                return int(candidate)
        except (TypeError, ValueError):
            continue
    return None


def _retry_after(error: Exception) -> float | None:
    value = getattr(error, "retry_after", None)
    response = getattr(error, "response", None)
    headers = getattr(response, "headers", None)
    if value is None and headers:
        value = headers.get("retry-after") or headers.get("Retry-After")
    try:
        return max(0.0, float(value)) if value is not None else None
    except (TypeError, ValueError):
        return None


def is_retryable(error: Exception) -> bool:
    code = _status_code(error)
    message = str(error).lower()
    return code in {429, 500, 502, 503, 504} or any(
        marker in message
        for marker in (
            "rate limit",
            "too many requests",
            "temporarily unavailable",
            "service unavailable",
            "timed out waiting for the gemini request lock",
        )
    )


def run_gemini_request(operation: Callable[[], T], operation_name: str) -> T:
    """Run one Gemini request with cross-process serialization and backoff."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        lock = None
        try:
            # Entity extraction, topic naming, and recommendations can run in
            # separate processes. Serialize requests so they do not amplify a
            # provider rate limit against the same API key.
            try:
                lock = get_redis().lock(
                    LOCK_NAME,
                    timeout=LOCK_TIMEOUT_SECONDS,
                    blocking_timeout=LOCK_WAIT_SECONDS,
                )
                if not lock.acquire():
                    raise RuntimeError("Timed out waiting for the Gemini request lock")
            except (RedisConnectionError, RedisTimeoutError) as lock_error:
                # Redis coordinates concurrent callers in production, but a
                # local API/test process should still be able to call Gemini
                # when the optional cache service is unavailable.
                lock = None
                logger.warning("Gemini request coordination unavailable; proceeding without lock: %s", lock_error)
            return operation()
        except Exception as error:
            if not is_retryable(error) or attempt >= MAX_ATTEMPTS:
                raise
            retry_after = _retry_after(error)
            exponential = min(MAX_DELAY_SECONDS, BASE_DELAY_SECONDS * (2 ** (attempt - 1)))
            delay = min(MAX_DELAY_SECONDS, retry_after if retry_after is not None else exponential)
            delay += random.uniform(0, min(1.0, delay * 0.25))
            logger.warning(
                "Gemini %s failed on attempt %s/%s; retrying in %.1fs: %s",
                operation_name,
                attempt,
                MAX_ATTEMPTS,
                delay,
                error,
            )
            time.sleep(delay)
        finally:
            if lock is not None:
                try:
                    lock.release()
                except Exception:
                    logger.debug("Gemini request lock was already released", exc_info=True)
    raise RuntimeError(f"Gemini {operation_name} failed after retries")
