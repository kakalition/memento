"""An example channel factory. Register it with ``app.channel("example", ExampleChannel)``.

A channel returns a ``Service`` (a blocking ``run()``); the built-in Telegram /
Slack / Email / Discord gateways are registered automatically by
``FullStackProvider`` when their tokens are configured.
"""

from __future__ import annotations

from typing import Any

from agentkit.supervise import Service


def ExampleChannel(app: Any) -> Service:
    def run() -> None:
        # Long-poll or listen here; call ``await app.answer(conversation_id, text)``
        # for each inbound message, then deliver the result back to the transport.
        app.settings  # noqa: B018 - placeholder

    return Service(name="example", run=run)
