from agents import Agent, RunContextWrapper, handoff
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

from context import CustomerServiceAgentChatContext
from .guardrail_agents import relevance_guardrail, jailbreak_guardrail

GENERAL_AGENT_MODEL = "gpt-5.2"

"""
Placeholder on_handoff callbacks

Note: Could be used for logging etc. For this demo, they are just placeholders to illustrate where
such logic would go.
"""

def on_order_cancellation_handoff(
        context: RunContextWrapper[CustomerServiceAgentChatContext], 
    ):
    pass

def on_order_tracking_handoff( context: RunContextWrapper[CustomerServiceAgentChatContext], 
    ):
    pass


# Define agents first (with empty handoffs)
redirection_agent = Agent[CustomerServiceAgentChatContext](
    name="Redirection Agent",
    model=GENERAL_AGENT_MODEL,
    handoff_description="Sends a given request to a specialist agent for handling.",
    instructions=(
        f"{RECOMMENDED_PROMPT_PREFIX} "
        "You are a helpful customer service agent for an online order management service. Route the customer to the best agent: "
        "Order Changes for any changes to existing orders, Order Tracking for tracking existing orders," 
        "Other Inquiries for any other questions"
        "If the request is clear, hand off immediately and let the specialist complete multi-step work without asking the user to confirm after each tool call."
        "Never emit more than one handoff per message: do your prep (at most one tool call) and then hand off once."
    ),
    tools=[],
    handoffs=[],
    input_guardrails=[relevance_guardrail, jailbreak_guardrail],
)

order_cancellation_agent = Agent[CustomerServiceAgentChatContext](
    name="Order Cancellation Agent",
    model=GENERAL_AGENT_MODEL,
    handoff_description="Handles customer requests to cancel orders.",
    instructions=(
        f"{RECOMMENDED_PROMPT_PREFIX} "
        "You are a helpful customer service agent specializing in order cancellations. "
        "If a customer requests to cancel an order, confirm the order details, process the cancellation, and provide a clear confirmation message. "
        "If the order cannot be cancelled (e.g., already shipped), politely explain the situation and offer alternatives.;" \
        "return to the redirection agent if done or if the customer needs help with anything else"
    ),
    tools=[],
    handoffs=[],
    input_guardrails=[relevance_guardrail, jailbreak_guardrail],
)

order_tracking_agent = Agent[CustomerServiceAgentChatContext](
    name="Order Tracking Agent",
    model=GENERAL_AGENT_MODEL,
    handoff_description="Provides customers with order tracking information.",
    instructions=(
        f"{RECOMMENDED_PROMPT_PREFIX} "
        "You are a helpful customer service agent specializing in order tracking. "
        "When a customer asks about the status or location of their order, retrieve the latest tracking information and provide a concise, friendly update. "
        "If tracking is unavailable, apologize and offer to follow up or escalate as needed." \
        "return to the redirection agent if done or if the customer needs help with anything else"
    ),
    tools=[],
    handoffs=[],
    input_guardrails=[relevance_guardrail, jailbreak_guardrail],
)

# Now set up handoff relationships
redirection_agent.handoffs = [
    handoff(agent=order_cancellation_agent, on_handoff=on_order_cancellation_handoff),
    handoff(agent=order_tracking_agent, on_handoff=on_order_tracking_handoff),
]

order_cancellation_agent.handoffs.extend([
    handoff(agent=redirection_agent),
])

order_tracking_agent.handoffs.extend([
    handoff(agent=redirection_agent),
])
