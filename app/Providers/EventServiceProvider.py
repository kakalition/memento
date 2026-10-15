"""Registers events and their listeners."""

from __future__ import annotations

from typing import Any

from agentkit import Provider
from app.Listeners.IndexNoteOnSave import IndexNoteOnSave
from app.Listeners.LogNoteSaved import LogNoteSaved

LISTENERS = [IndexNoteOnSave, LogNoteSaved]


class EventServiceProvider(Provider):
    def register(self, app: Any) -> None:
        for listener_class in LISTENERS:
            listener = listener_class()
            for name in type(listener).events():
                app.on(name, listener)
