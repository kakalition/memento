"""The agent, built declaratively with ``Agent.make(...).full()``."""

from __future__ import annotations

from typing import Any

from agentkit import Agent
from app.Jobs.SyncNotes import SyncNotes
from app.Models.Note import Note
from app.Policies.MementoPolicy import memento_policy
from app.Tools.notes import (
    archive_note,
    capture_note,
    current_time,
    get_note,
    list_notes,
    search_notes,
    set_reminder,
    tag_note,
)

INSTRUCTIONS = (
    "You are memento, the owner's personal knowledge and notes assistant. "
    "Capture what matters, keep it tidy with tags, and help the owner find it "
    "again — by meaning (search_notes) as well as by keyword. Prefer the owner's "
    "own words when you summarize. When asked to remember something, capture a "
    "note; when asked to find something, search before answering. Setting a "
    "reminder is a durable one-off job; archiving a note requires approval."
)


def build_assistant(kb: Any = None) -> Agent:
    builder = (
        Agent.make("memento")
        .instructions(INSTRUCTIONS)
        .tool(current_time)
        .tool(capture_note)
        .tool(search_notes)
        .tool(list_notes)
        .tool(get_note)
        .tool(tag_note)
        .tool(archive_note, requires_approval=True)
        .tool(set_reminder)
        .database({"note": Note})            # CRUD over the allow-listed Note model
        .scheduler(["sync_notes", "digest", "remind"])
        .queue({"sync": SyncNotes})
        .learning()                            # reflect -> learn -> apply
    )
    if kb is not None:
        builder = builder.knowledge(kb)
    return (
        builder
        # The whole agent stack: persona + memory + skills + HITL + safety + the
        # settings-enabled native toolkits (each skipped when its flag disables it).
        .full()
        .policy(memento_policy())
        .output(str)
    )
