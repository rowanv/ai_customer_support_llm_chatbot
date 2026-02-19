from chatkit.agents import AgentContext
from pydantic import BaseModel




class AgentChatContext:
    """Lightweight stand-in for agent chat context used in tests.

    This avoids requiring the `openai-chatkit`/`chatkit` package during tests.
    """

    def __init__(self) -> None:
        self.state: dict[str, Any] = {}



class CustomerServiceAgentContext(BaseModel):
    """Context for airline customer service agents."""

    customer_name: str | None = None
    order_id: str | None = None
    language: str | None = None



class CustomerServiceAgentChatContext(AgentContext[dict]):
    """
    AgentContext wrapper used during ChatKit runs.
    Holds the persisted CustomerServiceAgentContext in `state`.
    """

    state: CustomerServiceAgentContext



def create_initial_agent_context() -> CustomerServiceAgentContext:
    """
    Factory for a new CustomerServiceAgentContext.
    Starts empty; values are populated during the conversation.
    """
    ctx = CustomerServiceAgentContext()
    return ctx



def public_context(ctx: CustomerServiceAgentContext) -> dict:
    """
    Return the context for UI display.
    NOTE: In a real implementation, this would filter out any sensitive information before returning.
    """
    data = ctx.model_dump()
    return data
