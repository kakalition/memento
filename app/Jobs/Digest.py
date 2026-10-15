"""A durable task: a weekly notes digest delivered into the conversation."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta
from typing import Any

from agentkit.logging import get_logger
from app.Notifications.NotesDigest import NotesDigest
from app.Support.delivery import deliver_conversation
from app.Support.notes import tag_list

STALE_DAYS = 30


def build_summary(notes: list[Any], *, now: datetime | None = None, period_days: int = 7) -> str:
    """Render a digest: notes captured, top tags, and notes left untouched."""
    now = now or datetime.now(UTC)
    window = now - timedelta(days=period_days)
    stale_before = now - timedelta(days=STALE_DAYS)
    active = [note for note in notes if not note.archived]
    captured = [note for note in active if _aware(note.created_at) >= window]
    stale = [note for note in active if _aware(note.updated_at) < stale_before]

    tags = Counter(tag for note in active for tag in tag_list(note.tags))
    top = ", ".join(f"{name} ({count})" for name, count in tags.most_common(5)) or "none yet"

    lines = [
        "Weekly notes digest",
        f"- Notes captured this week: {len(captured)}",
        f"- Active notes: {len(active)}",
        f"- Top tags: {top}",
    ]
    if stale:
        lines.append(f"- Stale notes (not touched in {STALE_DAYS} days): {len(stale)}")
    return "\n".join(lines)


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


async def run(conversation_id: str = "cli:default", period: str = "week") -> None:
    """Scheduler task entry point; writes the digest into the conversation."""
    from agentkit import scheduler
    from agentkit.runtime import repositories
    from app.Repositories import AppRepositories

    runtime = scheduler.ensure_configured(repos_factory=AppRepositories)
    async with repositories(runtime) as repos:
        notes = await repos.notes.active(include_archived=True)
        summary = build_summary(notes)
        await deliver_conversation(repos, conversation_id, NotesDigest(summary).content())
    get_logger("app").info("notes digest delivered to %s", conversation_id)


def register() -> None:
    from agentkit import scheduler

    scheduler.task("digest")(run)
