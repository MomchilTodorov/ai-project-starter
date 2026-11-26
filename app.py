import json
import logging
import re

from fastapi import Depends, FastAPI, HTTPException, Path, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Annotated, Literal

from ai_client import stream_gemini

from policy_demo import answer_policy_question

from product_tools import get_product

from contextlib import asynccontextmanager

from database import (
    init_db,
    create_conversation,
    get_conversations,
    get_messages,
    save_message,
    conversation_exists,
    reserve_demo_slot,
    update_conversation_title,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(format="%(levelname)s %(name)s %(message)s")
    logging.getLogger("policy_demo").setLevel(logging.INFO)
    init_db()
    yield


app = FastAPI(title="AI Project Starter", lifespan=lifespan)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    text: str = Field(min_length=1, max_length=10000)


class ChatRequest(BaseModel):
    conversation_id: int = Field(gt=0)
    message: str = Field(min_length=1, max_length=10000)


def get_demo_visitor(request: Request) -> str | None:
    return getattr(request.state, "demo_visitor_id", None)


DemoVisitor = Annotated[str | None, Depends(get_demo_visitor)]


def enforce_demo_prompt_limit(visitor_id: str | None, prompt: str):
    if visitor_id is None:
        return
    if len(prompt) > 1500:
        raise HTTPException(422, "Keep demo questions at 1,500 characters or fewer.")
    if not reserve_demo_slot(visitor_id, "prompt", visitor_limit=8, site_limit=60):
        raise HTTPException(
            429, "The demo's daily AI limit was reached. Try again tomorrow (UTC)."
        )


def catalog_price_reply(message: str) -> str | None:
    match = re.fullmatch(
        r"(?:what(?:['’]s| is) the price of|how much is)\s+product\s+([0-9]+)\s*\??",
        message.strip(),
        flags=re.IGNORECASE,
    )
    if match is None:
        return None

    try:
        product_id = int(match.group(1))
    except ValueError:
        return "I couldn't find that product in the catalog."

    product = get_product(product_id)
    if "error" in product:
        return f"I couldn't find product {product_id} in the catalog."

    return f"Product {product_id} costs {product['price']:.2f} {product['currency']}."


@app.post("/chat")
def chat(request: ChatRequest, visitor_id: DemoVisitor):

    if not conversation_exists(request.conversation_id, visitor_id):
        raise HTTPException(status_code=404, detail="Conversation not found")

    enforce_demo_prompt_limit(visitor_id, request.message)
    previous_messages = get_messages(request.conversation_id)

    history = [
        {"role": item["role"], "text": item["content"]}
        for item in previous_messages[-20:]
    ]

    def event_stream():
        chunks = []

        try:
            catalog_reply = catalog_price_reply(request.message)
            if catalog_reply is not None:
                reply_chunks = (catalog_reply,)
            else:
                reply_chunks = stream_gemini(
                    request.message, history, demo_mode=visitor_id is not None
                )

            for chunk in reply_chunks:
                chunks.append(chunk)

                data = json.dumps({"type": "chunk", "text": chunk})

                yield f"data: {data}\n\n"

            answer = "".join(chunks)

            # Save the completed exchange
            save_message(request.conversation_id, "user", request.message)

            save_message(request.conversation_id, "assistant", answer)

            if not previous_messages:
                title = request.message.strip()[:50]
                update_conversation_title(request.conversation_id, title)

            yield 'data: {"type":"done"}\n\n'

        except Exception:
            import traceback

            traceback.print_exc()

            data = json.dumps(
                {"type": "error", "message": "Could not complete the AI response."}
            )

            yield f"data: {data}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )


@app.post("/conversations")
def new_conversation(visitor_id: DemoVisitor):
    if visitor_id and not reserve_demo_slot(
        visitor_id, "conversation", visitor_limit=5, site_limit=120
    ):
        raise HTTPException(
            429,
            "The demo's daily new-chat limit was reached. Try again tomorrow (UTC).",
        )
    conversation_id = create_conversation("New Chat", visitor_id)

    return {"id": conversation_id, "title": "New Chat"}


@app.get("/conversations")
def list_conversations(visitor_id: DemoVisitor):
    return {"conversations": get_conversations(visitor_id)}


@app.get("/conversations/{conversation_id}/messages")
def conversation_messages(conversation_id: int, visitor_id: DemoVisitor):
    if not conversation_exists(conversation_id, visitor_id):
        if visitor_id is None:
            return {"messages": []}
        raise HTTPException(404, "Conversation not found")
    messages = get_messages(conversation_id)

    return {"messages": messages}


@app.get("/products/{product_id}/price")
def product_price(product_id: int = Path(gt=0)):
    product = get_product(product_id)

    if "error" in product:
        raise HTTPException(status_code=404, detail="Product not found")

    return {
        "product_id": product_id,
        "price": product["price"],
        "currency": product["currency"],
    }


class PolicyQuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=10000)


@app.post("/policy/answer")
def policy_answer(
    request: PolicyQuestionRequest, visitor_id: DemoVisitor
) -> dict[str, str | None]:
    enforce_demo_prompt_limit(visitor_id, request.question)
    return answer_policy_question(request.question, demo_mode=visitor_id is not None)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
