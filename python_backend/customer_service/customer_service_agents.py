import httpx

from typing_extensions import TypedDict
from typing import Optional, Any, Dict

from agents import Agent, RunContextWrapper, handoff, function_tool
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

from python_backend.context import CustomerServiceAgentChatContext
from .guardrail_agents import relevance_guardrail, jailbreak_guardrail


GENERAL_AGENT_MODEL = "gpt-5.2"


HUMAN_IN_LOOP = "Please call 888-888-8888, where our team will be readily able to help you with any order issues."


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


class OrderInfo(TypedDict, total=False):
    order_id: str
    email: str


@function_tool
async def fetch_tracking(ctx: RunContextWrapper[CustomerServiceAgentChatContext], order_id: Optional[str] = None, customer_email: Optional[str] = None) -> Dict[str, Any]:
    """Fetch tracking info for an order and return the order JSON.

    Tries arguments first, then falls back to values in `ctx.state` and
    `ctx.request_context` if available. Delegates to the central
    `service_fetch_order` client which performs the HTTP request.
    """
    # fallback to context
    try:
        if not order_id:
            st = getattr(ctx, "state", None)
            if st is not None:
                order_id = getattr(st, "order_id", None) or order_id
    except Exception:
        pass

    try:
        if not customer_email:
            req = getattr(ctx, "request_context", None) or {}
            if isinstance(req, dict):
                headers = req.get("headers", {}) or {}
                customer_email = headers.get("X-Customer-Email") or headers.get("x-customer-email") or customer_email
            st = getattr(ctx, "state", None)
            if st is not None and not customer_email:
                customer_email = getattr(st, "customer_email", None) or customer_email
    except Exception:
        pass

    if not order_id or not customer_email:
        return {"error": "missing_order_id_or_email"}
    
    base_url = "http://localhost:8000"
    url = f"{base_url.rstrip('/')}/api/v1/orders/{order_id}/"
    headers = {"X-Customer-Email": customer_email}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, headers=headers)
    except Exception as exc:
        return {"error": {"type": "network_error", "detail": str(exc)}}

    if resp.status_code == 200:
        try:
            data = resp.json()
        except Exception:
            return {"error": {"type": "invalid_json"}}
        # confirm the email matches
        try:
            order_email = data.get("customer_email") or data.get("email")
            if order_email and order_email != customer_email:
                return {"error": {"type": "email_mismatch"}}
        except Exception:
            pass
        return data
    else:
        return {"error": {"type": "http", "status": resp.status_code, "detail": resp.text}}



# Define agents first (with empty handoffs)
redirection_agent = Agent[CustomerServiceAgentChatContext](
    name="Redirection Agent",
    model=GENERAL_AGENT_MODEL,
    handoff_description="Sends a given request to a specialist agent for handling.",
    instructions=(
        f"{RECOMMENDED_PROMPT_PREFIX} "
        "You are a helpful customer service agent for an online order management service. Route the customer to the best agent: "
        "Order Changes for any changes to existing orders, Order Tracking for tracking existing orders," 
        "For any other questions, route to {HUMAN_IN_LOOP}."
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
        "If there is a problem pulling up the tracking information, redirect to {HUMAN_IN_LOOP}"
        "Return to the redirection agent if done or if the customer needs help with anything else."
    ),
    tools=[fetch_tracking],
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
