import httpx
from datetime import datetime, timedelta

from typing_extensions import TypedDict
from typing import Optional, Any, Dict

from agents import Agent, RunContextWrapper, handoff, function_tool
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

from python_backend.context import CustomerServiceAgentChatContext
from .guardrail_agents import relevance_guardrail, jailbreak_guardrail


GENERAL_AGENT_MODEL = "gpt-5.2"
BASE_API_URL = "http://localhost:8000"

HUMAN_IN_LOOP = "Please call 888-888-8888, where our team will be readily able to help you with any order issues."


"""
Placeholder on_handoff callbacks

Note: Could be used for logging etc. For this demo, they are just placeholders to illustrate where
such logic would go.
"""

def on_order_cancellation_handoff(
    context: RunContextWrapper[CustomerServiceAgentChatContext],
) -> None:
    pass

def on_order_tracking_handoff(
    context: RunContextWrapper[CustomerServiceAgentChatContext],
) -> None:
    pass


class OrderInfo(TypedDict, total=False):
    order_id: str
    id: str
    email: str
    customer_email: str
    status: str
    type: str
    datetime_placed: str
    placed_at: str
    created_at: str


@function_tool
async def get_order_info(ctx: RunContextWrapper[CustomerServiceAgentChatContext], order_id: Optional[str] = None, customer_email: Optional[str] = None) -> Dict[str, Any]:
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
    
    
    url = f"{BASE_API_URL.rstrip('/')}/api/v1/orders/{order_id}/"
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

@function_tool
async def cancel_order_or_enforce_policies(order_info: OrderInfo) -> Dict[str, Any]:
    """Enforce cancellation policies and attempt to cancel the order via the external API.

    `order_info` must include at least `order_id` and a customer email (either `email` or `customer_email`).
    Returns a dict with either `ok: True` and the updated `order` or an `error` object.
    """
    # Basic validations
    if not order_info:
        return {"error": {"type": "missing_order_info", "message": "Order info is required."}}

    status = (order_info.get("status") or "").lower()
    otype = (order_info.get("type") or "").lower()

    if status == "cancelled":
        return {"error": {"type": "order_cancelled", "message": "This order has already been cancelled."}}

    if "digital" in otype or "digital media" in otype:
        return {"error": {"type": "digital_media_restriction", "message": "Orders for digital media cannot be cancelled once placed."}}

    if status == "shipped":
        return {"error": {"type": "already_shipped", "message": "This order has already been shipped and cannot be cancelled. If you would like to return the item once it arrives, we can assist with the return process."}}

    # check cancellation window (expect ISO string or datetime)
    placed = order_info.get("datetime_placed") or order_info.get("placed_at") or order_info.get("created_at")
    try:
        if isinstance(placed, str):
            # Support ISO strings with trailing Z (UTC) and offsets
            iso = placed.replace("Z", "+00:00")
            placed_dt = datetime.fromisoformat(iso)
        elif isinstance(placed, datetime):
            placed_dt = placed
        else:
            placed_dt = None
    except Exception:
        placed_dt = None

    if placed_dt is not None:
        if datetime.now() - placed_dt > timedelta(days=15):
            return {"error": {"type": "cancellation_window_expired", "message": "The cancellation window for this order has expired."}}

    # prepare PATCH request
    order_id = order_info.get("order_id") or order_info.get("id")
    customer_email = order_info.get("customer_email") or order_info.get("email")
    if not order_id or not customer_email:
        return {"error": {"type": "missing_order_id_or_email", "message": "Order id and customer email are required to cancel an order."}}

    url = f"{BASE_API_URL.rstrip('/')}/api/v1/orders/{order_id}/"
    headers = {"X-Customer-Email": customer_email}
    payload = {"status": "cancelled"}

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.patch(url, json=payload, headers=headers)
    except Exception as exc:
        return {"error": {"type": "network_error", "detail": str(exc), "redirect": HUMAN_IN_LOOP}}

    if resp.status_code in (200, 201, 204):
        # ideally return the updated order JSON
        try:
            data = resp.json() if resp.content else {**order_info, "status": "cancelled"}
        except Exception:
            data = {**order_info, "status": "cancelled"}
        return {"ok": True, "order": data}
    else:
        # map HTTP failures to structured errors
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        return {"error": {"type": "http", "status": resp.status_code, "detail": detail, "redirect": HUMAN_IN_LOOP}}

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
    tools=[get_order_info, cancel_order_or_enforce_policies],
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
    tools=[get_order_info],
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
