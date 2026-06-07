"""Recursive character text splitter, 512-token chunks with 50-token overlap."""

from __future__ import annotations

import re

_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


def split_text(text: str, chunk_size: int = 512, chunk_overlap: int = 50) -> list[str]:
    """Split text using recursive character strategy."""
    chunks: list[str] = []
    _split_recursive(text.strip(), chunk_size, chunk_overlap, _SEPARATORS, chunks)
    return [c for c in chunks if c.strip()]


def _split_recursive(
    text: str,
    chunk_size: int,
    chunk_overlap: int,
    separators: list[str],
    result: list[str],
) -> None:
    if _token_count(text) <= chunk_size:
        result.append(text)
        return

    separator = separators[0] if separators else ""
    remaining_seps = separators[1:] if separators else []

    splits = re.split(re.escape(separator), text) if separator else list(text)

    current: list[str] = []
    current_tokens = 0

    for split in splits:
        split_tokens = _token_count(split)

        if current_tokens + split_tokens > chunk_size and current:
            chunk = separator.join(current)
            result.append(chunk)
            # retain overlap: drop from front until within overlap budget
            while current and current_tokens > chunk_overlap:
                removed = current.pop(0)
                current_tokens -= _token_count(removed)

        current.append(split)
        current_tokens += split_tokens

    if current:
        leftover = separator.join(current)
        if _token_count(leftover) <= chunk_size:
            result.append(leftover)
        else:
            _split_recursive(leftover, chunk_size, chunk_overlap, remaining_seps, result)


def _token_count(text: str) -> int:
    # Approximate: 1 token ≈ 4 chars (avoids tiktoken import overhead in tests)
    return max(1, len(text) // 4)
