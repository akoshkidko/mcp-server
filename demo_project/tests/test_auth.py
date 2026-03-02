"""Tests for authentication helpers."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from demo_project.src.auth import hash_password, verify_password, generate_token, is_valid_token


def test_password_round_trip():
    hashed = hash_password("hunter2")
    assert verify_password("hunter2", hashed)
    assert not verify_password("wrong", hashed)


def test_generate_token_length():
    token = generate_token("user-123")
    assert len(token) == 64


def test_is_valid_token_accepts_64_chars():
    token = "a" * 64
    assert is_valid_token(token)


def test_is_valid_token_rejects_short():
    assert not is_valid_token("short")
