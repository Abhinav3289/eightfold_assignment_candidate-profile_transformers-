"""Field extraction helpers for nested paths."""

from __future__ import annotations

import re
from typing import Any


def get_by_path(data: Any, path: str) -> Any:
    """Resolve dotted/bracket paths like emails[0] or skills[].name."""
    if not path:
        return data
    tokens = re.findall(r"[^.\[\]]+|\[\]|\[\d+\]", path)
    current = data
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token == "[]":
            if not isinstance(current, list):
                return None
            if i + 1 < len(tokens):
                next_token = tokens[i + 1]
                collected: list[Any] = []
                for item in current:
                    value = item.get(next_token) if isinstance(item, dict) else getattr(item, next_token, None)
                    if value is not None:
                        collected.append(value)
                return collected
            return current
        index_match = re.fullmatch(r"\[(\d+)\]", token)
        if index_match:
            idx = int(index_match.group(1))
            if not isinstance(current, list) or idx >= len(current):
                return None
            current = current[idx]
        else:
            if isinstance(current, dict):
                current = current.get(token)
            else:
                current = getattr(current, token, None)
        if current is None:
            return None
        i += 1
    return current
