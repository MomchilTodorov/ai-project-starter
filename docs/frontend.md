# React Frontend

## Technology
- React for the user interface
- Vite for development
- FastAPI for the Python backend
- Gemini for AI responses

## Architecture
React -> FastAPI -> Gemini

## API Communication
The frontend uses fetch() to send JSON messages
to the FastAPI /chat endpoint.

During development, Vite can proxy /api/chat
to http://127.0.0.1:8000/chat.

## Next Steps
- Build the chat interface
- Display conversation history
- Add loading states
- Handle API errors
