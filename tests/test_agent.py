"""The built agent exposes the expected tools/toolkits and can capture a note."""

from __future__ import annotations

from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import FunctionModel

CUSTOM = {
    "current_time",
    "capture_note",
    "search_notes",
    "list_notes",
    "get_note",
    "tag_note",
    "archive_note",
    "set_reminder",
}

NATIVE = {
    "db_find",
    "db_get",
    "db_create",
    "db_delete",
    "schedule_task",
    "list_schedules",
    "enqueue_task",
    "enqueue_job",
    "notify",
    "notify_me",
    "list_conversations",
    "search_history",
    "usage_summary",
    "audit_trail",
    "index_document",
    "save_skill",
}

CAPABILITIES = {
    "remember",
    "recall",
    "search_knowledge",
    "list_skills",
    "learn",
    "reflect",
    "list_lessons",
}


def test_built_agent_exposes_tools_and_toolkits(agent_app):
    tools = set(agent_app.agent()._function_toolset.tools)
    assert tools >= CUSTOM
    assert tools >= NATIVE
    assert tools >= CAPABILITIES


async def test_turn_captures_a_note(agent_app, repos, deps):
    def model_fn(messages, info):
        for message in messages:
            for part in getattr(message, "parts", []):
                if isinstance(part, ToolReturnPart):
                    return ModelResponse(parts=[TextPart("Saved it.")])
        return ModelResponse(
            parts=[
                ToolCallPart(
                    "capture_note",
                    {"title": "Idea", "body": "ship memento", "tags": "work"},
                )
            ]
        )

    result = await agent_app.agent().run(
        "remember to ship memento", deps=deps, model=FunctionModel(model_fn)
    )
    assert "Saved" in result.output

    notes = await repos.notes.all()
    assert notes and notes[0].title == "Idea"
    assert notes[0].tags == "work"


async def test_persona_is_in_the_instructions(agent_app, repos, deps):
    captured: dict[str, str | None] = {}

    def model_fn(messages, info):
        captured["instructions"] = info.instructions
        return ModelResponse(parts=[TextPart("ok")])

    await agent_app.agent().run(
        "hello", deps=deps, model=FunctionModel(model_fn)
    )
    assert "memento" in (captured["instructions"] or "").lower()
