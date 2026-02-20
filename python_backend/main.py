
from chatkit.server import StreamingResult
from fastapi import FastAPI, Request
from fastapi.responses import Response, StreamingResponse

from python_backend.memory_store import CustomerServiceChatkitStore
from python_backend.server import CustomerServiceServer
from python_backend.server_local_dev_api import register_local_external_api

app = FastAPI()




server = CustomerServiceServer(store=CustomerServiceChatkitStore())


@app.get("/health")
async def health() -> dict:
    return {"status": "healthy"}


@app.post("/chatkit")
async def chatkit_endpoint(request: Request):
    result = await server.process(await request.body(), context={})
    if isinstance(result, StreamingResult):
        return StreamingResponse(result, media_type="text/event-stream")
    return Response(content=result.json, media_type="application/json")


# Register local external API used during development/testing
try:
    register_local_external_api(app)
except Exception:
    # Non-fatal during import in environments where this isn't available
    pass

__all__ = [
    "app",
]
