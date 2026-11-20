import json

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Literal

from ai_client import stream_gemini

app = FastAPI(title="AI Project Starter")


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    text: str = Field(min_length=1, max_length=10000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10000)
    history: list[ChatMessage] = Field(
        default_factory=list,
        max_length=20
    )


@app.post("/chat")
def chat(request: ChatRequest):

    history = [
        item.model_dump()
        for item in request.history
    ]

    def event_stream():
        try:
            for chunk in stream_gemini(request.message, history):
                data = json.dumps({"type": "chunk", "text": chunk})
                yield f"data: {data}\n\n"

            yield 'data: {"type":"done"}\n\n'

        except Exception:
            import traceback

            traceback.print_exc()

            data = json.dumps({
                "type": "error",
                "message": "AI service is unavailable."
            })

            yield f"data: {data}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"}
    )
