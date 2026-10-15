"""Schedules and durable tasks are registered as the kernel/full-stack intend."""

from __future__ import annotations

from types import SimpleNamespace


def _ctx(deps):
    return SimpleNamespace(deps=deps)


async def test_kernel_schedules_registered(agent_app, repos):
    names = {job.name for job in await repos.schedules.list()}
    assert {"sync-notes", "weekly-digest"} <= names


async def test_core_schedules_are_not_duplicated(agent_app, repos):
    names = [job.name for job in await repos.schedules.list()]
    assert names.count("memory-consolidate") == 1
    assert names.count("learning-reflect") == 1


def test_durable_tasks_registered(agent_app):
    from agentkit import scheduler

    assert {"sync_notes", "digest", "remind"} <= set(scheduler.TASKS)


async def test_digest_is_weekly_on_monday(agent_app, repos):
    jobs = {job.name: job for job in await repos.schedules.list()}
    digest = jobs["weekly-digest"]
    assert digest.kind == "cron"
    assert digest.schedule == "0 8 * * 1"


async def test_set_reminder_registers_a_one_off(agent_app, repos, deps):
    from app.Tools.notes import set_reminder

    await set_reminder(_ctx(deps), "call mum", "2030-01-01T09:00")
    jobs = [job for job in await repos.schedules.list() if job.task == "remind"]
    assert len(jobs) == 1
    assert jobs[0].kind == "once"
    assert "call mum" in jobs[0].args


async def test_set_reminder_rejects_bad_datetime(agent_app, deps):
    from app.Tools.notes import set_reminder

    result = await set_reminder(_ctx(deps), "x", "not-a-date")
    assert result.startswith("ERROR")
