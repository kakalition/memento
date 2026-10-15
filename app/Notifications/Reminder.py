"""A reminder notification."""

from __future__ import annotations

from agentkit import Notification


class Reminder(Notification):
    channels = ("log", "conversation")

    def __init__(self, message: str) -> None:
        self.message = message

    def content(self) -> str:
        return f"Reminder: {self.message}"
