from chatkit.server import StreamingResult, ChatKitServer
from chatkit.types import (
    ThreadItemDoneEvent,
    ThreadMetadata,
    UserMessageItem,
    AssistantMessageItem,
    AssistantMessageContent,
    ThreadStreamEvent,
)


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
    