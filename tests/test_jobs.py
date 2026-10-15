"""The durable digest and reminder tasks, and the digest summary builder."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from app.Jobs.Digest import build_summary
from app.Jobs.Digest import run as digest_run
from app.Jobs.Remind import run as remind_run
from app.Repositories import AppRepositories


def test_build_summary_counts_recent_tags_and_stale():
    now = datetime(2026, 1, 10, tzinfo=UTC)
    notes = [
        SimpleNamespace(
            archived=False,
            tags="work,idea",
            created_at=now - timedelta(days=1),
            updated_at=now - timedelta(days=1),
        ),
        SimpleNamespace(
            archived=False,
            tags="work",
            created_at=now - timedelta(days=40),
            updated_at=now - timedelta(days=40),
        ),
        SimpleNamespace(archived=True, tags="work", created_at=now, updated_at=now),
    ]

    summary = build_summary(notes, now=now)

    assert "Notes captured this week: 1" in summary
    assert "Active notes: 2" in summary
    assert "work (2)" in summary
    assert "Stale notes" in summary


def _configure(agent_app):
    from agentkit import scheduler

    scheduler.configure(agent_app.settings, repos_factory=AppRepositories)


async def test_remind_task_delivers(agent_app):
    _configure(agent_app)
    await remind_run("call mum", "cli:default")

    async with agent_app.repositories() as repos:
        rows = await repos.messages.list("cli:default")
    assert any("call mum" in row.payload for row in rows)


async def test_digest_task_delivers(agent_app):
    _configure(agent_app)
    async with agent_app.repositories() as repos:
        await repos.notes.create(title="Recipe", body="chili con carne", tags="food")

    await digest_run("cli:default")

    async with agent_app.repositories() as repos:
        rows = await repos.messages.list("cli:default")
    assert any("Weekly notes digest" in row.payload for row in rows)
