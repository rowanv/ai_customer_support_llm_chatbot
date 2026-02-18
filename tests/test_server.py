import importlib.util
import pathlib
import sys
import pytest

from chatkit.server import StreamingResult
from fastapi.testclient import TestClient


# Load the FastAPI app from python-backend/main.py by file path
root = pathlib.Path(__file__).resolve().parents[1]
backend_dir = root / "python-backend"
# Ensure python-backend is on sys.path so its `customer_service` package imports work
sys.path.insert(0, str(backend_dir))

main_path = backend_dir / "main.py"
spec = importlib.util.spec_from_file_location("app_module", str(main_path))
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)

client = TestClient(app_module.app)





def test_server_exists():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "healthy"}

def test_chatkit_post_returns_200_and_valid_json():
    payload = b'{}'
    response = client.post("/chatkit", data=payload)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith(("application/json", "text/event-stream"))

def test_chatkit_post_invalid_payload_returns_4xx():
    payload = b'{invalid json'
    response = client.post("/chatkit", data=payload)
    assert 400 <= response.status_code < 500

def test_chatkit_post_streamingresult(monkeypatch):
    server = app_module.server
    class DummyStream(StreamingResult):
        def __aiter__(self):
            return self
        async def __anext__(self):
            raise StopAsyncIteration
    monkeypatch.setattr(server, "process", lambda *a, **kw: DummyStream())
    response = client.post("/chatkit", data=b'{}')
    assert response.headers["content-type"].startswith("text/event-stream")

def test_cors_headers_present():
    response = client.options("/chatkit", headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST"
    })
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
