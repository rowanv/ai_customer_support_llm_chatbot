import importlib.util
import pathlib
import sys

from fastapi.testclient import TestClient


# Load the FastAPI app from python-backend/main.py by file path
root = pathlib.Path(__file__).resolve().parents[1]
backend_dir = root / "python-backend"
# Ensure python-backend is on sys.path so its `customer_service` package imports work
sys.path.insert(0, str(backend_dir))

# Provide a lightweight stub for `openai_agents` if it's not importable in the test
import types
if importlib.util.find_spec("openai_agents") is None:
    fake = types.ModuleType("openai_agents")
    class _DummyAgent:
        pass
    fake.Agent = _DummyAgent
    fake.RunContextWrapper = _DummyAgent
    sys.modules["openai_agents"] = fake

main_path = backend_dir / "main.py"
spec = importlib.util.spec_from_file_location("app_module", str(main_path))
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)

client = TestClient(app_module.app)


def test_server_exists():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "healthy"}
