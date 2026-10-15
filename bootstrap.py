"""The application entry point.

``agentkit serve`` boots ``bootstrap:app``, so this is the single place your app is
assembled: settings, the repository container, and the service providers.
``FullStackProvider`` wires the whole stack (config sections, the daily
``memory:consolidate`` schedule, and any configured channels).
"""

from __future__ import annotations

from agentkit import App, FullStackProvider
from app.config import Settings
from app.Providers.AppServiceProvider import AppServiceProvider
from app.Providers.EventServiceProvider import EventServiceProvider
from app.Repositories import AppRepositories

app = App(name="memento", settings=Settings, repos_factory=AppRepositories)
app.providers([EventServiceProvider, AppServiceProvider, FullStackProvider])
