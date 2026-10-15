"""Pytest root.

Keeps tests hermetic: a temporary agent home and the offline ``hash`` embedder, so
nothing touches your real data or the network. Each test gets a freshly reloaded
app so its database is isolated.
"""

from __future__ import annotations

import importlib
import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

os.environ.setdefault("AGENT_HOME", tempfile.mkdtemp(prefix="memento-test-"))
os.environ.setdefault("MEMORY_EMBEDDING_BACKEND", "hash")
os.environ.setdefault("OBSERVABILITY", "off")
os.environ.setdefault("WEBUI_ENABLED", "false")


@pytest.fixture
def agent_app(tmp_path, monkeypatch):
    """A freshly booted memento app backed by a per-test temporary home."""
    monkeypatch.setenv("AGENT_HOME", str(tmp_path))
    monkeypatch.setenv("MEMORY_EMBEDDING_BACKEND", "hash")
    monkeypatch.setenv("OBSERVABILITY", "off")
    monkeypatch.setenv("WEBUI_ENABLED", "false")

    from agentkit.config import get_settings

    get_settings.cache_clear()

    import bootstrap

    importlib.reload(bootstrap)
    application = bootstrap.app
    application.boot()
    return application


@pytest.fixture
async def repos(agent_app):
    async with agent_app.repositories() as opened:
        yield opened


@pytest.fixture
def deps(agent_app, repos):
    from agentkit.deps import Deps

    payload = Deps(settings=agent_app.settings, repos=repos)
    payload.extras["app"] = agent_app
    payload.extras["conversation_id"] = "test:1"
    return payload
