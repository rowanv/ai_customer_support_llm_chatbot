"""Fakes and fixtures for testing agents

Enables us to fake OpenAI Agents components.
"""

import pytest
from datetime import datetime, timedelta


@pytest.fixture
def sample_order():
    return {
        "order_id": "123",
        "created_at": datetime.now() - timedelta(days=5),
        "status": "processing",
        "amount": 200
    }


@pytest.fixture
def sample_baseline_policy():
    return [
        {
            "id": "standard_cancellation_window",
            "max_days": 10,
            "priority": 3
        }
    ]


@pytest.fixture
def sample_user_flagged_policy():
    return[
        {
            "id": "fraud_flag_restriction",
            "type": "fraud_block",
            "block_actions": ["cancel_order"],
            "priority": 0
        }
    ]



@pytest.fixture(scope="module")
def fake_agents():
    """Inject a lightweight fake `agents` package into sys.modules for tests.

    Yields the fake module object so tests can customize behavior (e.g., Runner.run).
    """
    import types
    import sys

    fake = types.ModuleType("agents")

    class Agent:
        def __class_getitem__(cls, item):
            return cls

        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    class RunContextWrapper:
        pass

    class GuardrailFunctionOutput:
        def __init__(self, output_info, tripwire_triggered: bool):
            self.output_info = output_info
            self.tripwire_triggered = tripwire_triggered

    def input_guardrail(name=None):
        def decorator(f):
            return f

        return decorator

    fake.Agent = Agent
    fake.RunContextWrapper = RunContextWrapper
    fake.GuardrailFunctionOutput = GuardrailFunctionOutput
    fake.input_guardrail = input_guardrail
    def function_tool(func=None, **kwargs):
        # no-op decorator that supports both @function_tool and @function_tool(...)
        if func is None:
            def _decorator(f):
                return f

            return _decorator
        return func

    fake.function_tool = function_tool
    fake.TResponseInputItem = object
    
    class Runner:
        @staticmethod
        async def run(*args, **kwargs):
            class _R:
                def final_output_as(self, _model):
                    return {}

            return _R()

    fake.Runner = Runner

    ext_pkg = types.ModuleType("agents.extensions")
    hp = types.ModuleType("agents.extensions.handoff_prompt")
    hp.RECOMMENDED_PROMPT_PREFIX = "[RECOMMENDED]"
    ext_pkg.handoff_prompt = hp

    # Provide a `handoff` factory function and lightweight Handoff object so
    # tests that call `from agents import handoff` or
    # `from agents.handoffs import handoff` behave like the real SDK.
    class _Handoff:
        def __init__(self, agent=None, on_handoff=None, description=None, **kwargs):
            self.agent = agent
            self.target_agent = agent
            self.on_handoff = on_handoff
            self.description = description

    def handoff(agent=None, on_handoff=None, description=None, **kwargs):
        return _Handoff(agent=agent, on_handoff=on_handoff, description=description, **kwargs)

    fake.handoff = handoff
    # also expose a small agents.handoffs module
    handoffs_mod = types.ModuleType("agents.handoffs")
    handoffs_mod.handoff = handoff

    # Provide a minimal `chatkit.agents.AgentContext` so imports in
    # production code succeed during tests without requiring the real package.
    chatkit_mod = types.ModuleType("chatkit")
    chatkit_agents = types.ModuleType("chatkit.agents")
    class AgentContext:
        def __class_getitem__(cls, item):
            return cls
    chatkit_agents.AgentContext = AgentContext

    # Also expose the fake under the top-level `agents` package name so code
    # that imports `agents` (installed distribution) will pick up the fake
    # during tests.
    sys.modules["agents"] = fake
    sys.modules["agents.handoffs"] = handoffs_mod
    sys.modules["agents.extensions"] = ext_pkg
    sys.modules["agents.extensions.handoff_prompt"] = hp
    sys.modules["chatkit"] = chatkit_mod
    sys.modules["chatkit.agents"] = chatkit_agents

    try:
        yield fake
    finally:
        # Clean up injected modules
        for name in (
            "chatkit.agents",
            "chatkit",
            "agents.extensions.handoff_prompt",
            "agents.extensions",
            "agents.handoffs",
            "agents",
        ):
            sys.modules.pop(name, None)
