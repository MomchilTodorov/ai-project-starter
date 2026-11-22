
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from product_tools import get_product

load_dotenv()

# 1. Define the tool schema
product_function = types.FunctionDeclaration(
    name="get_product",
    description="Retrieve a product by its numeric ID.",
    parameters_json_schema={
        "type": "object",
        "properties": {
            "product_id": {
                "type": "integer",
                "description": "Product ID to look up"
            }
        },
        "required": ["product_id"],
        "additionalProperties": False
    }
)

tool = types.Tool(
    function_declarations=[product_function]
)


def run_demo():
    client = genai.Client(
        api_key=os.environ["GEMINI_API_KEY"]
    )

    model = os.environ["GEMINI_MODEL"]
    question = "What's the price of product 123?"

    try:
        # 2. Ask Gemini what to do
        response = client.models.generate_content(
            model=model,
            contents=question,
            config=types.GenerateContentConfig(
                tools=[tool]
            )
        )

        calls = response.function_calls or []

        if not calls:
            print("Gemini answered without using a tool:")
            print(response.text)
            return

        # 3. Execute only approved functionsrole
        tool_results = []

        for call in calls:
            print("Requested function:", call.name)
            print("Arguments:", call.args)

            if call.name != "get_product":
                raise ValueError("Unapproved function")

            args = dict(call.args or {})

            product_id = args.get("product_id")

            if type(product_id) is not int or product_id <= 0:
                raise ValueError("Invalid product ID")

            result = get_product(product_id)

            print("Tool result:", result)

            tool_results.append(
                types.Part.from_function_response(
                    name="get_product",
                    response={"result": result}
                )
            )

        # 4. Send the tool results back to Gemini
        final_response = client.models.generate_content(
            model=model,
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=question)]
                ),
                response.candidates[0].content,
                types.Content(
                    role="user",
                    parts=tool_results
                )
            ],
            config=types.GenerateContentConfig(
                tools=[tool]
            )
        )

        # 5. Display final answer
        if final_response.function_calls:
            print("Gemini requested another tool round.")
        else:
            print("Final answer:", final_response.text)

    finally:
        client.close()


if __name__ == "__main__":
    run_demo()
