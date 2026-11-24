import logging
import os
from time import perf_counter

from dotenv import load_dotenv
from google import genai
from google.genai import types

from store_policies import retrieve_policy


logger = logging.getLogger(__name__)


def answer_policy_question(question: str) -> dict[str, str | None]:
    policy = retrieve_policy(question)
    if policy is None:
        logger.info("Policy lookup found no match")
        return {"answer": "I couldn't find a relevant store policy.", "source": None}

    logger.info("Policy lookup selected %s", policy["source"])

    load_dotenv()
    model = os.environ["GEMINI_MODEL"]
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    try:
        started_at = perf_counter()
        response = client.models.generate_content(
            model=model,
            contents=f"Policy text:\n{policy['text']}\n\nQuestion:\n{question}",
            config=types.GenerateContentConfig(
                system_instruction=(
                    "Answer using only the supplied policy text. "
                    "If the policy doesn't answer the question, say so."
                )
            ),
        )
        elapsed_ms = (perf_counter() - started_at) * 1000
        logger.info("Gemini responded in %.0f ms", elapsed_ms)

        return {
            "answer": response.text or "I couldn't generate a policy answer.",
            "source": policy["source"],
        }
    finally:
        client.close()


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s %(message)s")
    logger.setLevel(logging.INFO)

    question = input("Ask a store policy question: ")
    result = answer_policy_question(question)
    print(result["answer"])
    if result["source"]:
        print(f"Source: {result['source']}")