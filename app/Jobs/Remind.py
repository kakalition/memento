"""A durable one-off task: deliver a scheduled reminder into the conversation."""

from __future__ import annotations

from agentkit.logging import get_logger
from app.Notifications.Reminder import Reminder
from app.Support.delivery import deliver_conversation


async def run(message: str, conversation_id: str = "cli:default") -> None:
    """Scheduler task entry point; writes the reminder into the conversation."""
    from agentkit import scheduler
    from agentkit.runtime import repositories
    from app.Repositories import AppRepositories

    runtime = scheduler.ensure_configured(repos_factory=AppRepositories)
    async with repositories(runtime) as repos:
        await deliver_conversation(repos, conversation_id, Reminder(message).content())
    get_logger("app").info("reminder delivered to %s: %s", conversation_id, message)


def register() -> None:
    from agentkit import scheduler

    scheduler.task("remind")(run)
