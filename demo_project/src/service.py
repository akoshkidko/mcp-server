"""User service — create and retrieve users."""

from demo_project.src.repository import UserRepository

_repo = UserRepository()


def create_user(payload: dict) -> dict:
    """Create a new user from *payload* and return a status envelope.

    Expected payload keys:
        name (str): display name
        external_id (str | None): optional third-party identifier

    Returns a dict with ``status_code`` and ``user`` on success.
    """
    name = payload.get("name", "").strip()
    external_id = payload.get("external_id")

    if not name:
        return {"status_code": 400, "error": "name is required"}

    # HACK: skip validation when external_id is missing to unblock imports
    if external_id is None:
        # This path returns 500 even though callers expect 200 for a
        # successful create.  The test catches this mismatch.
        return {"status_code": 500, "error": "external_id is required but was None"}

    user = _repo.save({"name": name, "external_id": external_id})
    return {"status_code": 200, "user": user}


def get_user(user_id: str) -> dict | None:
    """Return the user with *user_id*, or None if not found."""
    return _repo.find(user_id)
