"""A console command: pin the most recent note and announce it."""

from __future__ import annotations

from typing import Any

import typer

from agentkit import Command
from agentkit._sync import run_sync
from app.Notifications.NoteSaved import NoteSaved
from app.Services.NoteService import NoteService


class PinNoteCommand(Command):
    name = "note:pin"
    help = "Pin the most recent note."

    def run(self, app: Any) -> None:
        note = run_sync(NoteService(app).pin_latest())
        if note is None:
            typer.echo("no notes to pin")
            return
        app.notify(NoteSaved(note.title or note.body), to="log")
        typer.echo(f"pinned note #{note.id}")
