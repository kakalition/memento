"""A durable job: re-index notes into the knowledge base.

Runs on the scheduler (every 15 minutes) and the queue to repair knowledge-base
drift: edited notes are replaced, archived notes are forgotten.
"""

from __future__ import annotations

from typing import Any

from agentkit import Job
from agentkit.knowledge import chunk_text
from agentkit.logging import get_logger
from app.Support.notes import index_text


async def reindex(repos: Any) -> int:
    """Re-index every active note; drop archived notes from recall."""
    notes = await repos.notes.active(include_archived=True)
    active = 0
    for note in notes:
        source = f"note:{note.id}"
        if note.archived:
            await repos.knowledge.clear(source)
            continue
        await repos.knowledge.replace(source, chunk_text(index_text(note)))
        active += 1
    return active


class SyncNotes(Job):
    queue = "default"
    max_retries = 3

    async def handle(self, app: Any) -> None:
        async with app.repositories() as repos:
            count = await reindex(repos)
        get_logger("app").info("sync notes: indexed %s note(s)", count)


async def run() -> None:
    """Scheduler task entry point (runs in a worker; resolves its own runtime)."""
    from agentkit import scheduler
    from agentkit.runtime import repositories
    from app.Repositories import AppRepositories

    runtime = scheduler.ensure_configured(repos_factory=AppRepositories)
    async with repositories(runtime) as repos:
        count = await reindex(repos)
    get_logger("app").info("sync notes: indexed %s note(s)", count)


def register() -> None:
    from agentkit import scheduler

    scheduler.task("sync_notes")(run)
