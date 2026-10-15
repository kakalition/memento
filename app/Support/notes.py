"""Tag normalisation and the text memento indexes for semantic recall."""

from __future__ import annotations

from typing import Any

__all__ = ["index_text", "normalize_tags", "tag_list"]


def normalize_tags(value: Any) -> str:
    """Normalise tags to a stable, deduped, lowercase, comma-separated string."""
    if not value:
        raw: list[str] = []
    elif isinstance(value, str):
        raw = value.replace(",", " ").split()
    else:
        raw = []
        for item in value:
            raw.extend(str(item).replace(",", " ").split())
    seen: list[str] = []
    for token in raw:
        tag = token.strip().lower()
        if tag and tag not in seen:
            seen.append(tag)
    return ",".join(seen)


def tag_list(value: Any) -> list[str]:
    """Split a stored tags string into individual tags."""
    return [tag for tag in str(value or "").split(",") if tag]


def index_text(note: Any) -> str:
    """The text memento indexes into the knowledge base for one note."""
    parts = [getattr(note, "title", "") or "", getattr(note, "body", "") or ""]
    tags = tag_list(getattr(note, "tags", ""))
    if tags:
        parts.append("tags: " + ", ".join(tags))
    return "\n".join(part for part in parts if part).strip()
