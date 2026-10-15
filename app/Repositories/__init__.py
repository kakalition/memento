"""Repositories and the container that holds them."""

from __future__ import annotations

from agentkit.db.repositories import Repositories
from app.Repositories.NoteRepository import NoteRepository


class AppRepositories(Repositories):
    """Extra repositories are declared here and attached automatically."""

    repositories = {"notes": NoteRepository}


__all__ = ["AppRepositories", "NoteRepository"]
