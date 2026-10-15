"""The periodic notes digest notification."""

from __future__ import annotations

from agentkit import Notification


class NotesDigest(Notification):
    channels = ("log", "conversation")

    def __init__(self, summary: str) -> None:
        self.summary = summary

    def content(self) -> str:
        return self.summary
