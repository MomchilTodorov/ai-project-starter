from fastapi import FastAPI
from pydantic import BaseModel, Field
from ai_client import ask_gemini

app = FastAPI(title="AI Project Starter")

class ChatRequest(BaseModel):
    message: str = Field(min_length=1)

@app.post("/chat")
def chat(request: ChatRequest):
    return {"reply": ask_gemini(request.message)}
