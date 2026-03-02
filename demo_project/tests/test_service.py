"""Tests for the user service."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from demo_project.src.service import create_user


def test_create_user_with_external_id():
    result = create_user({"name": "Alice", "external_id": "ext-001"})
    assert result["status_code"] == 200
    assert result["user"]["name"] == "Alice"


def test_create_user():
    """Regression test: create_user with no external_id must return 200.

    Currently FAILS because service.py returns 500 for missing external_id.
    This test documents the expected contract.
    """
    result = create_user({"name": "Alex", "external_id": None})
    # BUG: returns 500 — tracked in service.py HACK comment
    assert result["status_code"] == 200, (
        f"Expected 200 but got {result['status_code']}: {result.get('error')}"
    )
