"""In-memory user repository — placeholder for a real database layer."""

import uuid


class UserRepository:
    """Simple dict-backed store; data is lost on restart."""

    # TODO: replace in-memory storage with a real database repository

    def __init__(self) -> None:
        self._store: dict[str, dict] = {}

    def save(self, data: dict) -> dict:
        user_id = str(uuid.uuid4())
        record = {"id": user_id, **data}
        self._store[user_id] = record
        return record

    def find(self, user_id: str) -> dict | None:
        return self._store.get(user_id)

    def all(self) -> list[dict]:
        return list(self._store.values())
