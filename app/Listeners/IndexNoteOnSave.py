"""Index a note into the knowledge base whenever it is saved.

An async listener so it can await the knowledge write. It reuses the turn's
repository handle (passed on the event) to avoid a second SQLite session
mid-turn; without a handle it logs and skips (``sync_notes`` repairs drift).
"""

from __future__ import annotations

from typing import Any

from agentkit import Listener
from agentkit.knowledge import chunk_text
from agentkit.logging import get_logger


class IndexNoteOnSave(Listener):
    event = "note.saved"

    async def handle(self, event: Any) -> None:
        note_id = event.get("note_id")
        repos = event.get("repos")
        if note_id is None:
            return
        if repos is None:
            get_logger("app").warning("note.saved without a repos handle; skipping index")
            return
        parts = [event.get("title") or "", event.get("text") or ""]
        tags = event.get("tags") or ""
        if tags:
            parts.append("tags: " + ", ".join(t for t in str(tags).split(",") if t))
        payload = "\n".join(part for part in parts if part).strip()
        try:
            await repos.knowledge.replace(f"note:{note_id}", chunk_text(payload))
        except Exception:  # pragma: no cover - indexing must not break the turn
            get_logger("app").exception("failed to index note #%s", note_id)
