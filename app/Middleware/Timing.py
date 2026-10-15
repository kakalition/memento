"""Logs each turn's duration (a ``Middleware``)."""

from __future__ import annotations

import time

from agentkit import Middleware
from agentkit.logging import get_logger


class Timing(Middleware):
    async def handle(self, turn, call_next):  # noqa: ANN001, ANN201
        start = time.perf_counter()
        result = await call_next()
        get_logger("app").info(
            "turn %s took %.3fs", turn.conversation_id, time.perf_counter() - start
        )
        return result
