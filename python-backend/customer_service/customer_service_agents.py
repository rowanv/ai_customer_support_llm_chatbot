from agents import Agent, RunContextWrapper
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

from .context import AgentChatContext
from .guardrail_agents import relevance_guardrail, jailbreak_guardrail

GENERAL_AGENT_MODEL = "gpt-5.2"

redirection_agent = Agent[AgentChatContext](
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

