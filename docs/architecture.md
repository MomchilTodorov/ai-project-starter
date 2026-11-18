# AI Application Architecture

Frontend: React / JavaScript
Backend: Python + FastAPI
AI Provider: Google Gemini

## Request Flow

1. User sends a message from the frontend.
2. Uvicorn receives the HTTP request.
3. FastAPI validates the request.
4. Python calls Gemini through the SDK.
5. FastAPI returns the AI response as JSON.

## Future Improvements

- React chat interface
- Streaming responses
- Error handling
- RAG document search
- Authentication and rate limiting
- Docker deployment
