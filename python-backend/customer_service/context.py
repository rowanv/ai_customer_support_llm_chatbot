from __future__ import annotations as _annotations

from typing import Any


class AgentChatContext:
    """Lightweight stand-in for agent chat context used in tests.

    This avoids requiring the `openai-chatkit`/`chatkit` package during tests.
    """

    def __init__(self) -> None:
        self.state: dict[str, Any] = {}


class UserConversationContext:
    """Stores context on a per session basis"""

    user_name: str | None = None
    user_email: str | None = None
    user_zip_code: str | None = None
    order_id: str | None = None


def create_initial_agent_context() -> AgentChatContext:
    """Factory for a new AgentChatContext."""
    return AgentChatContext()

