
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()


def stream_gemini(message: str, history: list):

    if os.getenv("MOCK_AI", "false").lower() == "true":
        for word in f"Mock AI response to: {message}".split():
            yield word + " "
        return

    client = genai.Client(
        api_key=os.environ["GEMINI_API_KEY"]
    )

    contents = []

    for item in history:
        role = "model" if item["role"] == "assistant" else "user"

        contents.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=item["text"])]
            )
        )

    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=message)]
        )
    )

    try:
        stream = client.models.generate_content_stream(
            model=os.environ["GEMINI_MODEL"],
            contents=contents
        )

        for chunk in stream:
            if chunk.text:
                yield chunk.text

    finally:
        client.close()
