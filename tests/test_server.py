import importlib.util
import pathlib
import sys

from fastapi.testclient import TestClient


# Load the FastAPI app from python-backend/main.py by file path
root = pathlib.Path(__file__).resolve().parents[1]
backend_dir = root / "python_backend"
# Ensure python_backend is on sys.path so its `customer_service` package imports work
sys.path.insert(0, str(backend_dir))

main_path = backend_dir / "main.py"
spec = importlib.util.spec_from_file_location("app_module", str(main_path))
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)

client = TestClient(app_module.app)


def test_server_exists():
    # The application exposes only the `/chatkit` endpoint in main.py.
    # GET is not allowed on `/chatkit` (POST-only), so expect 405.
    resp = client.get("/chatkit")
    assert resp.status_code == 405


def test_chatkit_post_returns_json_when_server_returns_json(monkeypatch):
    class DummyJSON:
        json = '{"ok": true}'

    async def _dummy_json(*a, **kw):
        return DummyJSON()

    server = app_module.server
    monkeypatch.setattr(server, "process", _dummy_json)

    response = client.post("/chatkit", data=b'{}')
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")


def test_chatkit_post_streamingresult(monkeypatch):
    server = app_module.server

    class DummyStream:
        def __aiter__(self):
            return self

        async def __anext__(self):
            raise StopAsyncIteration

    # Ensure the endpoint's isinstance check recognizes our dummy streaming result.
    monkeypatch.setattr(app_module, "StreamingResult", DummyStream, raising=False)

    async def _dummy_stream(*a, **kw):
        return DummyStream()

    monkeypatch.setattr(server, "process", _dummy_stream)

    response = client.post("/chatkit", data=b'{}')
    assert response.headers["content-type"].startswith("text/event-stream")


"""
Including this test for completeness to explicitly state that this app does not
set CORS headers -- if productionized, CORS configuration should be added in main.py and
this test updated accordingly.
"""
def test_cors_headers_not_present():
    # No CORS middleware is configured in main.py; OPTIONS should not include CORS headers.
    response = client.options("/chatkit", headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
    })
    assert response.headers.get("access-control-allow-origin") is None


def test_context_change_detection_detects_changes():
    from python_backend.context import CustomerServiceAgentContext

    prev = CustomerServiceAgentContext(customer_name="Marcus Henderson", order_id="123", language="en")
    new_context = {"customer_name": "Hana Suzuki", "order_id": "123", "language": "en"}
    prev_dict = prev.model_dump()
    changes = {k: new_context[k] for k in new_context if prev_dict.get(k) != new_context[k]}
    assert changes == {"customer_name": "Hana Suzuki"}


def test_context_change_detection_no_changes():
    from python_backend.context import CustomerServiceAgentContext

    prev = CustomerServiceAgentContext(customer_name="Marcus Henderson", order_id="123", language="en")
    new_context = {"customer_name": "Marcus Henderson", "order_id": "123", "language": "en"}
    prev_dict = prev.model_dump()
    changes = {k: new_context[k] for k in new_context if prev_dict.get(k) != new_context[k]}
    assert changes == {}
