import json
from unittest.mock import Mock

import pytest
from google.genai import models, types

from ai_client import review_chat_answer, stream_gemini


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


def test_reviewer_gets_question_draft_and_tool_results(monkeypatch):
    monkeypatch.delenv("MOCK_AI", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MODEL", "test-model")
    client = Mock()
    client.models.generate_content.return_value = Mock(text="  I could not verify gift wrapping.  ")
    client_factory = Mock(return_value=client)
    monkeypatch.setattr("ai_client.genai.Client", client_factory)
    evidence = [
        {"name": "lookup_store_policy", "result": {"error": "No matching store policy found."}}
    ]

    answer = review_chat_answer("Gift wrapping?", "Gift wrapping costs EUR 5.", evidence)

    assert answer == "I could not verify gift wrapping."
    client_factory.assert_called_once_with(api_key="test-key")
    request = client.models.generate_content.call_args.kwargs
    assert request["model"] == "test-model"
    assert json.loads(request["contents"]) == {
        "question": "Gift wrapping?",
        "draft": "Gift wrapping costs EUR 5.",
        "tool_results": evidence,
    }
    assert request["config"].tools is None
    client.close.assert_called_once()


def test_reviewer_rejects_empty_response_and_closes_client(monkeypatch):
    monkeypatch.delenv("MOCK_AI", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    client = Mock()
    client.models.generate_content.return_value = Mock(text=None)
    monkeypatch.setattr("ai_client.genai.Client", Mock(return_value=client))

    with pytest.raises(RuntimeError, match="empty review"):
        review_chat_answer("Gift wrapping?", "I don't know.", [])

    client.close.assert_called_once()
