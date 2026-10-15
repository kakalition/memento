"""The repository and service: capture, search, tag, archive."""

from __future__ import annotations

from app.Services.NoteService import NoteService


async def test_capture_normalizes_tags(agent_app):
    service = NoteService(agent_app)
    note = await service.capture("Groceries", "buy milk", "Shopping, home, shopping")
    assert note.id is not None
    assert note.tags == "shopping,home"
    assert note.source == "chat"


async def test_capture_and_list(agent_app):
    service = NoteService(agent_app)
    await service.capture("Groceries", "buy milk", "shopping")
    await service.capture("Standup", "daily sync", "work")
    titles = [note.title for note in await service.all()]
    assert titles == ["Standup", "Groceries"]


async def test_tag_and_archive(agent_app):
    service = NoteService(agent_app)
    note = await service.capture("Idea", "ship memento")

    tagged = await service.tag(note.id, "work, idea")
    assert tagged is not None and tagged.tags == "work,idea"

    archived = await service.archive(note.id)
    assert archived is not None
    assert (await service.get(note.id)).archived is True
    assert await service.all() == []


async def test_list_by_tag(agent_app):
    service = NoteService(agent_app)
    await service.capture("Groceries", "buy milk", "shopping")
    await service.capture("Standup", "daily sync", "work")
    tagged = await service.all(tag="shopping")
    assert [note.title for note in tagged] == ["Groceries"]


async def test_search_lexical_fallback(agent_app):
    service = NoteService(agent_app)
    await service.capture("Groceries", "buy oat milk", "shopping")
    result = await service.search("oat")
    assert "Groceries" in result


async def test_repository_scope_is_owner_scoped(agent_app, repos):
    await repos.notes.create(title="Mine", body="mine", tags="", source="cli")
    from app.Models.Note import Note

    repos.session.add(Note(owner_id="someone-else", title="Theirs", body="secret"))
    await repos.session.flush()

    mine = await repos.notes.all()
    assert [note.title for note in mine] == ["Mine"]
    assert await repos.notes.search_lexical("secret") == []
