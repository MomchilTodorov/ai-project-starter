from google.genai import models, types

from ai_client import stream_gemini


def test_chat_records_completed_tool_results_once(monkeypatch):
    monkeypatch.delenv("MOCK_AI", raising=False)
    monkeypatch.setenv("PUBLIC_DEMO_GEMINI_API_KEY", "test-key")
    responses = iter(
        [
            [types.Part.from_function_call(name="get_product", args={"product_id": 123})],
            [
                types.Part.from_function_call(
                    name="lookup_store_policy",
                    args={"question": "What is your gift-wrapping policy?"},
                )
            ],
            [types.Part.from_text(text="In stock. "), types.Part.from_text(text="Policy unavailable.")],
        ]
    )

    def fake_model_stream(self, *, model, contents, config):
        for part in next(responses):
            yield types.GenerateContentResponse(
                candidates=[
                    types.Candidate(content=types.Content(role="model", parts=[part]))
                ]
            )

    monkeypatch.setattr(
        models.Models, "_generate_content_stream_with_continuation", fake_model_stream
    )
    tool_results = []

    answer = "".join(
        stream_gemini(
            "Is product 123 in stock, and what is your gift-wrapping policy?",
            [],
            demo_mode=True,
            tool_results=tool_results,
        )
    )

    assert answer == "In stock. Policy unavailable."
    assert [item["name"] for item in tool_results] == ["get_product", "lookup_store_policy"]
    assert tool_results[0]["result"]["stock"] == 15
    assert tool_results[1]["result"] == {"error": "No matching store policy found."}
