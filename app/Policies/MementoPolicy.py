"""Memento's tool policy. Add tool names to ``deny`` to block them at runtime."""

from __future__ import annotations

from agentkit import ToolPolicy


def memento_policy() -> ToolPolicy:
    """The default policy: nothing denied here (writes are approval-gated)."""
    return ToolPolicy(deny=set())
