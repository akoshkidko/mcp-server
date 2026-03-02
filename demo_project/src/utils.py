"""Shared utility helpers."""

import logging

logger = logging.getLogger(__name__)


def safe_get(url: str, timeout: int = 5) -> dict | None:
    """Perform a GET request and return the JSON body, or None on error.

    TODO: add retry/backoff instead of silent fallback
    """
    try:
        import urllib.request
        import json as _json

        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return _json.loads(resp.read())
    except Exception as exc:  # noqa: BLE001
        logger.warning("safe_get(%s) failed silently: %s", url, exc)
        return None


def truncate(text: str, max_len: int = 100) -> str:
    """Return *text* truncated to *max_len* characters."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"
