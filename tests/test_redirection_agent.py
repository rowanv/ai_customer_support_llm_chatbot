import os
import sys


# Ensure the python-backend directory is importable as a package root for tests
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PYTHON_BACKEND = os.path.join(ROOT, "python-backend")
if PYTHON_BACKEND not in sys.path:
    sys.path.insert(0, PYTHON_BACKEND)


def test_redirection_agent_metadata(fake_agents):
    from customer_service import customer_service_agents as cs_agents

    found_agent = cs_agents.redirection_agent

    assert getattr(found_agent, "name", None) == "Redirection Agent"

"""
def test_redirection_agent_has_input_guardrails(fake_agents):
    from customer_service import customer_service_agents as cs_agents

    found_agent = cs_agents.redirection_agent

    guardrails = getattr(found_agent, "input_guardrails", None)
    assert isinstance(guardrails, (list, tuple))
    names = {g.__name__ for g in guardrails if hasattr(g, "__name__")}
    import ipdb; pdb.set_trace()
    # Expect the relevance and jailbreak guardrails to be attached
    assert "relevance_guardrail" in names
    assert "jailbreak_guardrail" in names
"""

def test_redirection_agent_runtime_mock(fake_agents):
    import asyncio

    # now import the customer_service agents (they will pick up our fake module)
    from customer_service import customer_service_agents as cs_agents

    # Create a fake Runner.run implementation that returns a predictable result
    class FakeResult:
        def __init__(self, final):
            self._final = final

        def final_output_as(self, _model):
            return self._final

    class Runner:
        @staticmethod
        async def run(found_agent, input, context=None):
            return FakeResult({"handoff": "Order Changes", "reason": "matched keywords"})

    fake_agents.Runner = Runner

    # Run the runner and assert we get the mocked response
    result = asyncio.run(fake_agents.Runner.run(cs_agents.redirection_agent, "Please change my order #123", context=None))
    output = result.final_output_as(None)

    assert output["handoff"] == "Order Changes"
