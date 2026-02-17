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
def fake_openai_agents():
    """Inject a lightweight fake `openai_agents` package into sys.modules for tests.

    Yields the fake module object so tests can customize behavior (e.g., Runner.run).
    """
    import types
    import sys

    fake = types.ModuleType("openai_agents")

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

    ext_pkg = types.ModuleType("openai_agents.extensions")
    hp = types.ModuleType("openai_agents.extensions.handoff_prompt")
    hp.RECOMMENDED_PROMPT_PREFIX = "[RECOMMENDED]"
    ext_pkg.handoff_prompt = hp

    sys.modules["openai_agents"] = fake
    sys.modules["openai_agents.extensions"] = ext_pkg
    sys.modules["openai_agents.extensions.handoff_prompt"] = hp

    try:
        yield fake
    finally:
        # Clean up injected modules
        for name in ("openai_agents.extensions.handoff_prompt", "openai_agents.extensions", "openai_agents"):
            sys.modules.pop(name, None)
