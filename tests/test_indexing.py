"""Notes are indexed into the knowledge base for semantic recall."""

from __future__ import annotations

from types import SimpleNamespace

from app.Jobs.SyncNotes import reindex
from app.Tools.notes import capture_note


def _ctx(deps):
    return SimpleNamespace(deps=deps)


async def test_capture_tool_indexes_into_knowledge(agent_app, repos, deps):
    result = await capture_note(_ctx(deps), "Groceries", "buy oat milk", "shopping")
    assert "Groceries" in result

    sources = await repos.knowledge.sources()
    assert any(source.startswith("note:") for source in sources)

    hits = await repos.knowledge.search("oat milk")
    assert hits
    assert any("oat milk" in hit.content for hit in hits)


async def test_search_notes_uses_the_index(agent_app, repos, deps):
    from app.Tools.notes import search_notes

    await capture_note(_ctx(deps), "Groceries", "buy oat milk", "shopping")
    result = await search_notes(_ctx(deps), "oat milk")
    assert "oat milk" in result


async def test_reindex_indexes_and_forgets(agent_app, repos):
    note = await repos.notes.create(title="Recipe", body="chili con carne", tags="food")
    count = await reindex(repos)
    assert count == 1
    assert f"note:{note.id}" in await repos.knowledge.sources()

    await repos.notes.update(note.id, archived=True)
    await reindex(repos)
    assert f"note:{note.id}" not in await repos.knowledge.sources()


async def test_archive_tool_removes_from_recall(agent_app, repos, deps):
    from app.Tools.notes import archive_note

    result = await capture_note(_ctx(deps), "Groceries", "buy oat milk", "shopping")
    note_id = int(result.split("#")[1].split(":")[0])

    await archive_note(_ctx(deps), note_id)
    assert f"note:{note_id}" not in await repos.knowledge.sources()
