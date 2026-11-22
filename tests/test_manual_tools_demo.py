from unittest.mock import Mock

from google.genai import types

import manual_tools_demo


def test_demo_withholds_price_when_gemini_skips_lookup(monkeypatch, capsys):
    client = Mock()
    client.models.generate_content.return_value = Mock(
        function_calls=[],
        text="Product 123 costs EUR 49.99.",
    )

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MODEL", "test-model")
    monkeypatch.setattr(
        manual_tools_demo.genai, "Client", Mock(return_value=client)
    )

    manual_tools_demo.run_demo()

    output = capsys.readouterr().out
    assert "I couldn't verify the price in the catalog." in output
    assert "49.99" not in output


def test_demo_sends_catalog_price_back_to_gemini(monkeypatch):
    tool_call = types.FunctionCall(
        name="get_product",
        args={"product_id": 123},
    )
    model_message = types.Content(
        role="model",
        parts=[types.Part(function_call=tool_call)],
    )

    client = Mock()
    client.models.generate_content.side_effect = [
        Mock(function_calls=[tool_call], candidates=[Mock(content=model_message)]),
        Mock(function_calls=[], text="Product 123 costs EUR 29.99."),
    ]

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MODEL", "test-model")
    monkeypatch.setattr(
        manual_tools_demo.genai, "Client", Mock(return_value=client)
    )

    manual_tools_demo.run_demo()

    assert client.models.generate_content.call_count == 2
    second_request = client.models.generate_content.call_args_list[1]
    tool_reply = second_request.kwargs["contents"][-1].parts[0].function_response

    assert tool_reply.name == "get_product"
    assert tool_reply.response["result"]["price"] == 29.99