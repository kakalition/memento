"""Logs every saved note (a ``Listener``)."""

from __future__ import annotations

from agentkit import Listener
from agentkit.logging import get_logger


class LogNoteSaved(Listener):
    event = "note.saved"

    def handle(self, event) -> None:  # noqa: ANN001
        get_logger("app").info("note saved #%s: %s", event.get("note_id"), event.get("title"))
