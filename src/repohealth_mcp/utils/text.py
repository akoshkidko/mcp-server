"""Text processing helpers for RepoHealth MCP.

Small, pure functions for normalising, truncating, and inspecting strings.
"""

import re


def truncate(text: str, max_length: int = 200, suffix: str = "…") -> str:
    """Return *text* truncated to *max_length* characters, appending *suffix* if cut."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from *text* (useful for cleaning CI log output)."""
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


def normalise_whitespace(text: str) -> str:
    """Collapse runs of whitespace to a single space and strip leading/trailing."""
    return re.sub(r"\s+", " ", text).strip()


def count_lines(text: str) -> int:
    """Return the number of lines in *text* (handles both \\n and \\r\\n)."""
    if not text:
        return 0
    return len(text.splitlines())


def extract_words(text: str) -> list[str]:
    """Return a list of lowercase alphanumeric words from *text*.

    Useful for lightweight token analysis without a heavy NLP dependency.
    """
    return re.findall(r"[a-z0-9]+", text.lower())
