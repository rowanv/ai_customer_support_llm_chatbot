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

    # Also expose the fake under the top-level `agents` package name so code
    # that imports `agents` (installed distribution) will pick up the fake
    # during tests.
    sys.modules["agents"] = fake
    sys.modules["agents.extensions"] = ext_pkg
    sys.modules["agents.extensions.handoff_prompt"] = hp

    try:
        yield fake
    finally:
        # Clean up injected modules
        for name in (
            "agents.extensions.handoff_prompt",
            "agents.extensions",
            "agents",
        ):
            sys.modules.pop(name, None)
