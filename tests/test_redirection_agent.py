import importlib.util
import os
import pathlib
import sys

# Ensure the repository root is importable so `python_backend` package loads
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PYTHON_BACKEND = os.path.join(ROOT, "python_backend")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def test_redirection_agent_metadata(fake_agents):
    # Load customer_service_agents module by file path to avoid package import issues
    root = pathlib.Path(__file__).resolve().parents[1]
    module_path = root / "python_backend" / "customer_service" / "customer_service_agents.py"
    spec = importlib.util.spec_from_file_location(
        "python_backend.customer_service.customer_service_agents",
        str(module_path),
    )
    cs_agents = importlib.util.module_from_spec(spec)
    # ensure relative imports inside the loaded module work
    cs_agents.__package__ = "python_backend.customer_service"
    spec.loader.exec_module(cs_agents)

    found_agent = cs_agents.redirection_agent

    assert getattr(found_agent, "name", None) == "Redirection Agent"
