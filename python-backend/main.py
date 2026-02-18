from datetime import datetime
from typing import AsyncIterator
import json
from typing import Any, Dict

from chatkit.server import StreamingResult, ChatKitServer
from chatkit.types import (
    ThreadItemDoneEvent,
    ThreadMetadata,
    UserMessageItem,
    AssistantMessageItem,
    AssistantMessageContent,
    ThreadStreamEvent,
)
from fastapi import Depends, FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse

from customer_service.customer_service_agents import (
    redirection_agent,
)

from customer_service.context import create_initial_agent_context
from memory_store import CustomerServiceChatkitStore

#from server import CustomerServiceServer

app = FastAPI()


class CustomerServiceServer(ChatKitServer):
    async def respond(
            self,
            thread: ThreadMetadata,
            input_user_message: UserMessageItem | None,
            context: dict,
    ) -> AsyncIterator[ThreadStreamEvent]:
        # Streams a fixed "Hello, world!" assistant message
        yield ThreadItemDoneEvent(
            item=AssistantMessageItem(
                thread_id=thread.id,
                id=self.store.generate_item_id("message", thread, context),
                created_at=datetime.now(),
                content=[AssistantMessageContent(text="Hello, world!")],
            ),
        )
    

server = CustomerServiceServer(store=CustomerServiceChatkitStore())


@app.post("/chatkit")
async def chatkit_endpoint(request: Request):
    result = await server.process(await request.body(), context={})
    if isinstance(result, StreamingResult):
        return StreamingResponse(result, media_type="text/event-stream")
    return Response(content=result.json, media_type="application/json")

__all__ = [
    "app",
    "redirection_agent",
]
