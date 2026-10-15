"""The note table — memento's single domain model."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Field

from agentkit import Model


def _now() -> datetime:
    return datetime.now(UTC)


class Note(Model, table=True):
    __tablename__ = "notes"

    id: int | None = Field(default=None, primary_key=True)
    owner_id: str = Field(index=True)
    title: str = ""
    body: str = ""
    tags: str = ""
    source: str = "chat"
    pinned: bool = False
    archived: bool = False
    created_at: datetime = Field(default_factory=_now, index=True)
    updated_at: datetime = Field(default_factory=_now)
