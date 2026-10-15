"""The notes domain service: capture, search, tag, archive.

Every method accepts an optional ``repos`` handle so agent tools can reuse the
turn's session (``ctx.deps.repos``) instead of opening a second one; when omitted
the service opens its own scope (used by jobs and the CLI).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from agentkit.foundation.service import Service
from app.Models.Note import Note
from app.Support.notes import normalize_tags, tag_list


class NoteService(Service):
    @asynccontextmanager
    async def _scope(self, repos: Any = None) -> AsyncIterator[Any]:
        if repos is not None:
            yield repos
            return
        async with self.repositories as opened:
            yield opened

    async def capture(
        self,
        title: str,
        body: str,
        tags: Any = "",
        source: str = "chat",
        *,
        repos: Any = None,
    ) -> Note:
        async with self._scope(repos) as r:
            return await r.notes.create(
                title=title.strip(),
                body=body.strip(),
                tags=normalize_tags(tags),
                source=source,
            )

    async def get(self, note_id: int, *, repos: Any = None) -> Note | None:
        async with self._scope(repos) as r:
            return await r.notes.get(note_id)

    async def all(
        self,
        *,
        tag: str | None = None,
        limit: int | None = None,
        include_archived: bool = False,
        repos: Any = None,
    ) -> list[Note]:
        async with self._scope(repos) as r:
            if tag:
                return await r.notes.by_tag(tag, limit=limit or 20)
            return await r.notes.active(limit, include_archived=include_archived)

    async def tag(self, note_id: int, tags: Any, *, repos: Any = None) -> Note | None:
        async with self._scope(repos) as r:
            note = await r.notes.get(note_id)
            if note is None:
                return None
            note.tags = normalize_tags(tags)
            await r.notes.update(note_id, tags=note.tags)
            return note

    async def archive(self, note_id: int, *, repos: Any = None) -> Note | None:
        async with self._scope(repos) as r:
            note = await r.notes.get(note_id)
            if note is None:
                return None
            await r.notes.update(note_id, archived=True)
            await r.knowledge.clear(f"note:{note_id}")
            return note

    async def pin_latest(self, *, repos: Any = None) -> Note | None:
        async with self._scope(repos) as r:
            note = await r.notes.recent(limit=1, include_archived=False)
            if not note:
                return None
            await r.notes.update(note[0].id, pinned=True)
            return note[0]

    async def search(self, query: str, limit: int = 5, *, repos: Any = None) -> str:
        query = (query or "").strip()
        if not query:
            return "Please provide something to search for."
        async with self._scope(repos) as r:
            hits = await r.knowledge.search(query, limit=limit)
            if hits:
                lines = [
                    f"[{i}] note {hit.source} #{hit.seq}\n{hit.content}"
                    for i, hit in enumerate(hits, start=1)
                ]
                return "\n\n".join(lines)
            notes = await r.notes.search_lexical(query, limit=limit)
            if not notes:
                return "No matching notes."
            return "\n".join(_format_note(note) for note in notes)


def _format_note(note: Note) -> str:
    tags = tag_list(note.tags)
    suffix = f" [{', '.join(tags)}]" if tags else ""
    flag = " (pinned)" if note.pinned else ""
    return f"#{note.id} {note.title}{suffix}{flag}\n{note.body}"
