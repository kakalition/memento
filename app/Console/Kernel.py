"""The console kernel: the schedule and the command list.

``app.schedule(...)`` is the fluent scheduler (Laravel's ``$schedule``). The
``memory:consolidate`` and ``learning:reflect`` schedules belong to
``FullStackProvider`` and are not repeated here.
"""

from __future__ import annotations

from typing import Any

from app.Console.Commands.PinNote import PinNoteCommand


class Kernel:
    def schedule(self, app: Any) -> None:
        app.schedule("sync_notes").name("sync-notes").every_fifteen_minutes().without_overlapping().description("Re-index notes into the knowledge base.")
        app.schedule("digest").name("weekly-digest").weekly_on(1, "08:00").description("Deliver the weekly notes digest.")

    def commands(self) -> list[Any]:
        return [PinNoteCommand()]
