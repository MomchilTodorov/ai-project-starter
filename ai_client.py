import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

def ask_gemini(message: str) -> str:
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
        contents=message,
    )
    return response.text or ""
