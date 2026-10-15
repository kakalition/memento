"""A custom validation rule: the value must contain non-whitespace."""

from __future__ import annotations

from typing import Any


def NonEmpty(value: Any) -> str | None:  # noqa: N802 - reads like a rule
    return None if str(value).strip() else "must not be blank"
