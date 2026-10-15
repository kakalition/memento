"""A notification sent when a note is saved (or pinned from the CLI)."""

from __future__ import annotations

from agentkit import Notification


class NoteSaved(Notification):
    channels = ("log",)

    def __init__(self, text: str) -> None:
        self.message = text

    def content(self) -> str:
        return f"Note saved: {self.message}"
