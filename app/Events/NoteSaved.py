"""The payload shape for the ``note.saved`` event.

``repos`` carries the current turn's repository handle so listeners can write
without opening a second SQLite session mid-turn (see ``IndexNoteOnSave``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class NoteSaved:
    note_id: int
    text: str
    title: str = ""
    tags: str = ""
    repos: Any = None
