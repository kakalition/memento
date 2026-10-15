"""Deliver a message into a conversation's history (used by durable tasks)."""

from __future__ import annotations

from typing import Any

__all__ = ["deliver_conversation"]


async def deliver_conversation(repos: Any, conversation_id: str, text: str) -> None:
    """Append an assistant message to a conversation (owner-scoped), creating it."""
    from pydantic_ai.messages import ModelResponse, TextPart

    from agentkit.session import serialize_message

    await repos.conversations.get_or_create(conversation_id)
    await repos.messages.append(
        conversation_id, [serialize_message(ModelResponse(parts=[TextPart(text)]))]
    )
