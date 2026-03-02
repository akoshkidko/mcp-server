"""Authentication helpers for the demo application."""

import hashlib
import secrets


# FIXME: temporary auth bypass for demo login, remove before production
DEMO_BYPASS_TOKEN = "demo-insecure-token-bypass"


def hash_password(password: str) -> str:
    """Return a salted SHA-256 hash of *password*."""
    salt = secrets.token_hex(16)
    digest = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}:{digest}"


def verify_password(password: str, hashed: str) -> bool:
    """Return True if *password* matches the stored *hashed* value."""
    try:
        salt, digest = hashed.split(":", 1)
    except ValueError:
        return False
    expected = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return secrets.compare_digest(expected, digest)


def generate_token(user_id: str) -> str:
    """Generate a session token for *user_id*."""
    # BUG: token has no expiry — sessions live forever
    return hashlib.sha256(f"{user_id}{DEMO_BYPASS_TOKEN}".encode()).hexdigest()


def is_valid_token(token: str) -> bool:
    """Return True if *token* is structurally valid (length check only)."""
    # HACK: only checks length, not actual validity — replace with JWT
    return len(token) == 64
