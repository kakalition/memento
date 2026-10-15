"""The application service provider (mandatory).

Binds the agent (with its shared knowledge base), config, middleware, commands,
schedule, native-toolkit allow-lists, and the durable tasks. ``register`` is for
declarations (no side effects); ``boot`` is for effects.
"""

from __future__ import annotations

from typing import Any

from agentkit import KnowledgeBase, Provider
from app.Agents.assistant import build_assistant
from app.config import AppSection
from app.Console.Kernel import Kernel
from app.Jobs.SyncNotes import SyncNotes
from app.Middleware.Timing import Timing
from app.Models.Note import Note

AGENT_TASKS = ["sync_notes", "digest", "remind"]


class AppServiceProvider(Provider):
    def register(self, app: Any) -> None:
        app.config("app", AppSection)

        kb = KnowledgeBase(app=app, settings=app.settings)
        app.container.instance("knowledge", kb)
        app.agent(build_assistant(kb))

        app.middleware(Timing())
        app.commands(Kernel().commands())
        Kernel().schedule(app)

        # Allow-lists the native toolkits read (the app, not the model, decides).
        app.models({"note": Note})
        app.agent_tasks(AGENT_TASKS)
        app.agent_jobs({"sync": SyncNotes})

    def boot(self, app: Any) -> None:
        # Register durable tasks before any init_scheduler() runs.
        from app.Jobs.Digest import register as register_digest
        from app.Jobs.Remind import register as register_remind
        from app.Jobs.SyncNotes import register as register_sync_notes

        register_sync_notes()
        register_digest()
        register_remind()
