import json

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Literal

from ai_client import stream_gemini

from contextlib import asynccontextmanager

from database import (
    init_db,
    create_conversation,
    get_conversations,
    get_messages,
    save_message,
    conversation_exists,
    update_conversation_title
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="AI Project Starter",
    lifespan=lifespan
)



class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    text: str = Field(min_length=1, max_length=10000)


class ChatRequest(BaseModel):
    conversation_id: int = Field(gt=0)
    message: str = Field(min_length=1, max_length=10000)



@app.post("/chat")
def chat(request: ChatRequest):

    if not conversation_exists(request.conversation_id):
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    previous_messages = get_messages(request.conversation_id)

    history = [
        {
            "role": item["role"],
            "text": item["content"]
        }
        for item in previous_messages[-20:]
    ]

    def event_stream():
        chunks = []

        try:
            for chunk in stream_gemini(request.message, history):
                chunks.append(chunk)

                data = json.dumps({
                    "type": "chunk",
                    "text": chunk
                })

                yield f"data: {data}\n\n"

            answer = "".join(chunks)

            # Save the completed exchange
            save_message(
                request.conversation_id,
                "user",
                request.message
            )

            save_message(
                request.conversation_id,
                "assistant",
                answer
            )

            if not previous_messages:
                title = request.message.strip()[:50]
                update_conversation_title(request.conversation_id, title)

            yield 'data: {"type":"done"}\n\n'

        except Exception:
            import traceback
            traceback.print_exc()

            data = json.dumps({
                "type": "error",
                "message": "Could not complete the AI response."
            })

            yield f"data: {data}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"}
    )




from fastapi import HTTPException


@app.post("/conversations")
def new_conversation():
    conversation_id = create_conversation("New Chat")

    return {
        "id": conversation_id,
        "title": "New Chat"
    }

@app.get("/conversations")
def list_conversations():
    return {"conversations": get_conversations()}


@app.get("/conversations/{conversation_id}/messages")
def conversation_messages(conversation_id: int):
    messages = get_messages(conversation_id)

    return {"messages": messages}


