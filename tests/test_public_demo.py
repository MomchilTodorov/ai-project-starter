from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from runpy import run_path
from sqlite3 import connect
from unittest.mock import Mock

import pytest
from fastapi import staticfiles
from fastapi.testclient import TestClient

import database
import policy_demo
from ai_client import stream_gemini


@pytest.fixture
def demo_config(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "chat.db")
    monkeypatch.setenv("PUBLIC_DEMO", "true")
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("GEMINI_MODEL", "test-model")
    monkeypatch.setenv("PUBLIC_DEMO_GEMINI_API_KEY", "test-public-key")
    monkeypatch.delenv("MOCK_AI", raising=False)
    (tmp_path / "index.html").write_text("Public demo", encoding="utf-8")
    static_files = staticfiles.StaticFiles
    monkeypatch.setattr(
        staticfiles, "StaticFiles", lambda **kwargs: static_files(directory=tmp_path, html=True)
    )


def load_production_app():
    production_file = Path(__file__).resolve().parents[1] / "production.py"
    return run_path(str(production_file))["app"]


def test_public_conversations_are_isolated_by_browser(demo_config, monkeypatch):
    mock_stream = Mock(return_value=iter(["Catalog answer"]))
    monkeypatch.setattr("app.stream_gemini", mock_stream)
    public_app = load_production_app()
    with (
        TestClient(public_app, base_url="https://testserver") as first,
        TestClient(public_app, base_url="https://testserver") as second,
    ):
        private_id = database.create_conversation("Private chat")
        database.save_message(private_id, "user", "Private message")
        assert first.get("/").status_code == 200
        assert first.get("/api/health").json() == {"status": "ok"}
        assert first.get("/api/conversations").json() == {"conversations": []}

        response = first.post("/api/conversations")
        chat_id = response.json()["id"]
        message = {"conversation_id": chat_id, "message": "What is the price?"}

        assert [row["id"] for row in first.get("/api/conversations").json()["conversations"]] == [chat_id]
        assert second.get("/api/conversations").json() == {"conversations": []}
        assert second.get(f"/api/conversations/{chat_id}/messages").status_code == 404
        assert first.get(f"/api/conversations/{private_id}/messages").status_code == 404
        assert second.post("/api/chat", json=message).status_code == 404
        mock_stream.assert_not_called()

        assert "Catalog answer" in first.post("/api/chat", json=message).text
        assert first.get(f"/api/conversations/{chat_id}/messages").json()["messages"][-1]["content"] == "Catalog answer"
        mock_stream.assert_called_once_with(message["message"], [], demo_mode=True)


def test_public_ai_limits_apply_across_chat_and_policy(demo_config, monkeypatch):
    answer_policy = Mock(return_value={"answer": "Within 30 days", "source": "Returns policy"})
    mock_stream = Mock()
    monkeypatch.setattr("app.answer_policy_question", answer_policy)
    monkeypatch.setattr("app.stream_gemini", mock_stream)
    with TestClient(load_production_app(), base_url="https://testserver") as client:
        chat_id = client.post("/api/conversations").json()["id"]
        assert client.post("/api/policy/answer", json={"question": "x" * 1501}).status_code == 422
        for _ in range(8):
            assert client.post("/api/policy/answer", json={"question": "Can I return this?"}).status_code == 200

        response = client.post("/api/chat", json={"conversation_id": chat_id, "message": "Hi"})
        assert response.status_code == 429
        assert "daily AI limit" in response.json()["detail"]
        assert client.get("/api/products/123/price").json()["price"] == 29.99

    assert answer_policy.call_count == 8
    mock_stream.assert_not_called()


def test_global_demo_limit_resists_concurrent_new_visitors(demo_config):
    database.init_db()
    with ThreadPoolExecutor(max_workers=8) as executor:
        reserved = list(executor.map(
            lambda visitor: database.reserve_demo_slot(str(visitor), "prompt", 8, 3),
            range(12),
        ))
    assert sum(reserved) == 3


def test_database_migration_preserves_existing_private_chats(demo_config):
    with connect(database.DB_PATH) as connection:
        connection.execute("""
            CREATE TABLE conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        connection.execute("INSERT INTO conversations (title) VALUES ('Existing chat')")
    database.init_db()
    database.init_db()
    assert database.get_conversations()[0]["title"] == "Existing chat"
    assert database.get_conversations("another-visitor") == []


def test_public_model_calls_use_dedicated_key_and_bounded_output(demo_config, monkeypatch):
    client = Mock()
    client.models.generate_content.return_value = Mock(text="Within 30 days")
    client.models.generate_content_stream.return_value = iter([Mock(text="Catalog answer")])
    factory = Mock(return_value=client)
    monkeypatch.setattr(policy_demo.genai, "Client", factory)

    assert list(stream_gemini("What is the price?", [], demo_mode=True)) == ["Catalog answer"]
    assert policy_demo.answer_policy_question("Can I return this?", demo_mode=True)["source"] == "Returns policy"
    assert factory.call_count == 2
    assert all(call.kwargs == {"api_key": "test-public-key"} for call in factory.call_args_list)
    chat_config = client.models.generate_content_stream.call_args.kwargs["config"]
    policy_config = client.models.generate_content.call_args.kwargs["config"]
    assert chat_config.max_output_tokens == policy_config.max_output_tokens == 512
    assert chat_config.automatic_function_calling.maximum_remote_calls == 2


def test_hosted_private_mode_still_requires_a_password(demo_config, monkeypatch):
    monkeypatch.delenv("PUBLIC_DEMO")
    monkeypatch.setenv("DEMO_PASSWORD", "private-test-password")
    with TestClient(load_production_app(), base_url="https://testserver") as client:
        assert client.get("/api/conversations").status_code == 401
        assert client.get("/", auth=("demo", "private-test-password")).status_code == 200
