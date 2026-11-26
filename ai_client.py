import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from product_tools import get_product
from store_policies import lookup_store_policy

load_dotenv()


def stream_gemini(message: str, history: list, *, demo_mode: bool = False):

    if os.getenv("MOCK_AI", "false").lower() == "true":
        for word in f"Mock AI response to: {message}".split():
            yield word + " "
        return

    key_name = "PUBLIC_DEMO_GEMINI_API_KEY" if demo_mode else "GEMINI_API_KEY"
    client = genai.Client(api_key=os.environ[key_name])

    contents = []

    for item in history:
        role = "model" if item["role"] == "assistant" else "user"

        contents.append(
            types.Content(role=role, parts=[types.Part.from_text(text=item["text"])])
        )

    contents.append(
        types.Content(role="user", parts=[types.Part.from_text(text=message)])
    )

    try:
        stream = client.models.generate_content_stream(
            model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
            contents=contents,
            config=types.GenerateContentConfig(
                tools=[get_product, lookup_store_policy],
                max_output_tokens=512 if demo_mode else None,
                automatic_function_calling=(
                    types.AutomaticFunctionCallingConfig(maximum_remote_calls=3)
                    if demo_mode
                    else None
                ),
                system_instruction=(
                    "You are a helpful shopping assistant. "
                    "Use get_product for catalog facts such as price and stock. "
                    "Use lookup_store_policy for questions about store rules. "
                    "If a question needs both, use both tools. "
                    "Name the policy source if you use one. "
                    "If a lookup fails, say what you could not verify."
                ),
            ),
        )

        for chunk in stream:
            if chunk.text:
                yield chunk.text

    finally:
        client.close()
