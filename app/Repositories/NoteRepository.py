"""Note persistence — CRUD is inherited from ``Repository``."""

from __future__ import annotations

from sqlalchemy import func, or_
from sqlmodel import select

from agentkit import Repository
from app.Models.Note import Note
from app.Support.notes import tag_list


class NoteRepository(Repository[Note]):
    model = Note

    async def latest(self) -> Note | None:
        return await self.where().latest("id").first()

    async def pinned(self) -> list[Note]:
        return await self.where(pinned=True).all()

    async def recent(self, limit: int = 20, *, include_archived: bool = False) -> list[Note]:
        query = self.where() if include_archived else self.where(archived=False)
        return await query.latest("id").limit(limit).all()

    async def by_tag(self, tag: str, limit: int = 20) -> list[Note]:
        wanted = tag.strip().lower()
        if not wanted:
            return []
        rows = await self.where(archived=False).latest("id").limit(500).all()
        return [note for note in rows if wanted in tag_list(note.tags)][:limit]

    async def active(self, limit: int | None = None, *, include_archived: bool = False) -> list[Note]:
        query = self.where() if include_archived else self.where(archived=False)
        query = query.latest("id")
        if limit is not None:
            query = query.limit(limit)
        return await query.all()

    async def search_lexical(self, query: str, limit: int = 5) -> list[Note]:
        needle = f"%{query.strip().lower()}%"
        stmt = (
            select(Note)
            .where(
                Note.owner_id == self.owner_id,
                Note.archived == False,  # noqa: E712
                or_(
                    func.lower(Note.title).like(needle),
                    func.lower(Note.body).like(needle),
                    func.lower(Note.tags).like(needle),
                ),
            )
            .order_by(Note.id.desc())  # type: ignore[arg-type]
            .limit(limit)
        )
        return list((await self.session.exec(stmt)).all())
