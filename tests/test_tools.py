"""Tool behavior, the native allow-list, and approval gating."""

from __future__ import annotations

from types import SimpleNamespace


def _ctx(deps):
    return SimpleNamespace(deps=deps)


def _fn(agent_app, name):
    return agent_app.agent()._function_toolset.tools[name].function


def test_approval_flags(agent_app):
    tools = agent_app.agent()._function_toolset.tools
    assert tools["archive_note"].requires_approval is True
    assert tools["db_delete"].requires_approval is True
    assert tools["schedule_task"].requires_approval is True
    assert tools["capture_note"].requires_approval is False
    assert tools["set_reminder"].requires_approval is False
    assert tools["db_find"].requires_approval is False


async def test_allow_list_rejects_unknown_model(agent_app, deps):
    result = await _fn(agent_app, "db_find")(_ctx(deps), "ghost", {})
    assert result.startswith("ERROR")


async def test_allow_list_permits_the_note_model(agent_app, repos, deps):
    await repos.notes.create(title="Groceries", body="buy milk", tags="shopping")
    result = await _fn(agent_app, "db_find")(_ctx(deps), "note", {})
    assert "Groceries" in result


async def test_capture_then_list_by_tag(agent_app, repos, deps):
    from app.Tools.notes import capture_note, list_notes

    await capture_note(_ctx(deps), "Groceries", "buy milk", "shopping")
    await capture_note(_ctx(deps), "Standup", "daily sync", "work")

    shopping = await list_notes(_ctx(deps), tag="shopping")
    assert "Groceries" in shopping
    assert "Standup" not in shopping


async def test_tag_note_tool(agent_app, repos, deps):
    from app.Tools.notes import capture_note, tag_note

    result = await capture_note(_ctx(deps), "Idea", "ship memento")
    note_id = int(result.split("#")[1].split(":")[0])

    assert "urgent" in await tag_note(_ctx(deps), note_id, "urgent")
    assert (await repos.notes.get(note_id)).tags == "urgent"


async def test_get_note_reports_missing(agent_app, deps):
    from app.Tools.notes import get_note

    assert "not found" in await get_note(_ctx(deps), 999)


async def test_capture_validates_input(agent_app, deps):
    from agentkit.foundation.validation import ValidationError
    from app.Tools.notes import capture_note

    try:
        await capture_note(_ctx(deps), "   ", "body")
    except ValidationError:
        pass
    else:  # pragma: no cover - the rule must reject a blank title
        raise AssertionError("blank title should fail validation")
