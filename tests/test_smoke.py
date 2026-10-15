"""A first test — the app boots and the agent exposes memento's tools."""

from __future__ import annotations

CUSTOM_TOOLS = {
    "current_time",
    "capture_note",
    "search_notes",
    "list_notes",
    "get_note",
    "tag_note",
    "archive_note",
    "set_reminder",
}


def test_app_boots(agent_app) -> None:
    assert agent_app.name == "memento"
    tools = set(agent_app.agent()._function_toolset.tools)
    assert tools >= CUSTOM_TOOLS
