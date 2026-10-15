"""Application settings and a layered config section."""

from __future__ import annotations

from agentkit import AgentSettings, Section


class Settings(AgentSettings):
    """Runtime settings (environment-driven). Extend as your app grows."""

    agent_name: str = "memento"


class AppSection(Section):
    """App-specific configuration.

    Precedence: ``defaults < config/app.py < environment``. Register it with
    ``app.config("app", AppSection)`` and read it with ``app.config("app")``.
    """

    env_prefix = "MEMENTO_"
    greeting: str = "Hello!"
