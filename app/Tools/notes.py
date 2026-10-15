"""Tools. The first argument is a RunContext[Deps]; the docstring is the schema."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from pydantic_ai import RunContext

from agentkit import emit, validate
from agentkit.deps import Deps
from app.Rules.NonEmpty import NonEmpty
from app.Services.NoteService import NoteService, _format_note


def _service(ctx: RunContext[Deps]) -> NoteService:
    return NoteService(ctx.deps.extras.get("app"))


async def current_time(ctx: RunContext[Deps]) -> str:
    """Return the current UTC time in ISO-8601 format."""
    return datetime.now(UTC).isoformat()


async def capture_note(
    ctx: RunContext[Deps], title: str, body: str, tags: str = ""
) -> str:
    """Save a note for the owner.

    Args:
        title: A short title for the note.
        body: The note contents.
        tags: Optional comma-separated tags.
    """
    validate(
        {"title": title, "body": body},
        {
            "title": ["required", "string", NonEmpty, "max:200"],
            "body": ["required", "string", NonEmpty, "max:5000"],
        },
    )
    service = _service(ctx)
    note = await service.capture(title, body, tags, "chat", repos=ctx.deps.repos)
    await emit(
        "note.saved",
        note_id=note.id,
        title=note.title,
        text=note.body,
        tags=note.tags,
        conversation_id=ctx.deps.conversation_id,
        repos=ctx.deps.repos,
    )
    return f"saved note #{note.id}: {note.title}"


async def search_notes(ctx: RunContext[Deps], query: str, limit: int = 5) -> str:
    """Search the owner's notes by meaning, falling back to keyword matching.

    Args:
        query: What to look for.
        limit: Maximum notes to return.
    """
    validate({"query": query}, {"query": ["required", "string", NonEmpty]})
    return await _service(ctx).search(query, limit=limit, repos=ctx.deps.repos)


async def list_notes(ctx: RunContext[Deps], tag: str | None = None, limit: int = 20) -> str:
    """List the owner's active notes, optionally filtered by tag.

    Args:
        tag: Only return notes carrying this tag.
        limit: Maximum notes to return.
    """
    notes = await _service(ctx).all(tag=tag, limit=limit, repos=ctx.deps.repos)
    if not notes:
        return "No notes yet."
    return "\n".join(_format_note(note) for note in notes)


async def get_note(ctx: RunContext[Deps], id: int) -> str:
    """Fetch one note by id.

    Args:
        id: The note id.
    """
    note = await _service(ctx).get(id, repos=ctx.deps.repos)
    if note is None:
        return f"note #{id} not found"
    tags = f" [{note.tags}]" if note.tags else ""
    return f"#{note.id} {note.title}{tags}\n{note.body}"


async def tag_note(ctx: RunContext[Deps], id: int, tags: str) -> str:
    """Replace the tags on a note.

    Args:
        id: The note id.
        tags: Comma-separated tags to set (replaces existing tags).
    """
    note = await _service(ctx).tag(id, tags, repos=ctx.deps.repos)
    if note is None:
        return f"note #{id} not found"
    return f"tagged note #{note.id} [{note.tags}]"


async def archive_note(ctx: RunContext[Deps], id: int) -> str:
    """Archive a note and remove it from semantic recall.

    Args:
        id: The note id.
    """
    note = await _service(ctx).archive(id, repos=ctx.deps.repos)
    if note is None:
        return f"note #{id} not found"
    await emit("note.archived", note_id=note.id)
    return f"archived note #{note.id}"


async def set_reminder(ctx: RunContext[Deps], message: str, at: str) -> str:
    """Schedule a durable reminder that will be delivered at a future time.

    Args:
        message: What to remind the owner about.
        at: When to remind, as an ISO-8601 datetime (e.g. 2026-11-01T09:00).
    """
    validate(
        {"message": message, "at": at},
        {"message": ["required", "string", NonEmpty], "at": ["required", "string", NonEmpty]},
    )
    try:
        moment = datetime.fromisoformat(at)
    except ValueError:
        return f"ERROR: could not parse 'at' as an ISO-8601 datetime: {at!r}"
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    args = json.dumps({"message": message, "conversation_id": ctx.deps.conversation_id})
    name = f"remind:{int(moment.timestamp())}"
    await ctx.deps.repos.schedules.upsert(
        name, kind="once", schedule=moment.isoformat(), task="remind", args=args
    )
    return f"reminder set for {moment.isoformat()}"
