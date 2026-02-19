import importlib.util
import pathlib
import sys

from fastapi.testclient import TestClient

# Load the FastAPI app from python-backend/main.py by file path
root = pathlib.Path(__file__).resolve().parents[2]
backend_dir = root / "python_backend"
# Ensure python_backend is on sys.path so its `server_local_dev_api` package imports work
sys.path.insert(0, str(backend_dir))

main_path = backend_dir / "main.py"
spec = importlib.util.spec_from_file_location("app_module", str(main_path))
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)

client = TestClient(app_module.app)


def test_get_order_success():
    headers = {"X-Customer-Email": "a123@gmail.com"}
    resp = client.get("/api/v1/orders/A123/", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["order_id"] == "A123"
    assert data["customer_email"] == "a123@gmail.com"
    assert "shipments" in data and isinstance(data["shipments"], list)


def test_get_order_missing_header():
    resp = client.get("/api/v1/orders/A123/")
    assert resp.status_code == 400


def test_get_order_mismatched_email():
    headers = {"X-Customer-Email": "other@example.com"}
    resp = client.get("/api/v1/orders/A123/", headers=headers)
    assert resp.status_code == 403


def test_get_order_not_found():
    headers = {"X-Customer-Email": "a123@gmail.com"}
    resp = client.get("/api/v1/orders/NOPE123/", headers=headers)
    assert resp.status_code == 404


def test_patch_order_success():
    headers = {"X-Customer-Email": "a123@gmail.com"}
    resp = client.patch("/api/v1/orders/A123/", json={"status": "cancelled"}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    # local API stores status in `status`
    assert data["order_id"] == "A123"
    assert data.get("status") == "cancelled"
