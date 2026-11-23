from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

import policy_demo
from app import app


@pytest.fixture
def gemini_factory(monkeypatch):
    factory = Mock()
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MODEL", "test-model")
    monkeypatch.setattr(policy_demo.genai, "Client", factory)
    return factory


@pytest.fixture
def api_client():
    # This route has no database dependency, so skip the app lifespan.
    client = TestClient(app)
    yield client
    client.close()


def test_policy_endpoint_sends_the_passage_and_returns_its_source(
    api_client, gemini_factory
):
    question = "How long do I have to return an item?"
    answer = "Unused items can be returned within 30 days of delivery."
    generate_content = gemini_factory.return_value.models.generate_content
    generate_content.return_value = Mock(text=answer)

    response = api_client.post("/policy/answer", json={"question": question})

    assert response.status_code == 200
    assert response.json() == {"answer": answer, "source": "Returns policy"}
    generate_content.assert_called_once()
    prompt = generate_content.call_args.kwargs["contents"]
    assert "Customers can return unused items within 30 days of delivery." in prompt
    assert question in prompt
    gemini_factory.return_value.close.assert_called_once()


def test_policy_endpoint_skips_gemini_when_no_policy_matches(api_client, gemini_factory):
    response = api_client.post("/policy/answer", json={"question": "What is Python?"})

    assert response.status_code == 200
    assert response.json() == {
        "answer": "I couldn't find a relevant store policy.",
        "source": None,
    }
    gemini_factory.assert_not_called()


def test_policy_endpoint_rejects_an_empty_question(api_client, gemini_factory):
    response = api_client.post("/policy/answer", json={"question": ""})

    assert response.status_code == 422
    gemini_factory.assert_not_called()
