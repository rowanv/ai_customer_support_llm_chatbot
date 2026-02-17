from __future__ import annotatios as _annotations 

from chatkit.agents import AgentContext 


class UserConversationContext():
    """Stores context on a per session basis"""

    user_name: str | None = None
    user_email: str | None = None
    user_zip_code: str | None = None
    order_id: str | None = None


def create_initial_agent_context() -> AgentContext:
    """
    Factory for a new AgentContext.
    Starts empty, values populated during conversation
    """
    context = AgentContext()
    return context 

