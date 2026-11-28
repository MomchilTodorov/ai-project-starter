import json
from unittest.mock import Mock

import pytest

from evaluate_chat_tools import CASES, evaluate, missing_checks


@pytest.mark.parametrize(
    ("policy_answer", "expected_missing"),
    [
        ("I could not verify the gift-wrapping policy.", []),
        ("I couldn’t find a gift-wrapping policy.", []),
        ("Our gift-wrapping policy charges EUR 5.", ["missing policy acknowledged"]),
    ],
    ids=["recorded-live-wording", "curly-apostrophe", "invented-fee"],
)
def test_gift_wrapping_evaluation_checks_policy_availability(
    policy_answer, expected_missing
):
    answer = f"Product 123 has 15 units available. {policy_answer}"

    assert missing_checks(answer, CASES[1][1]) == expected_missing


def test_missing_product_evaluation_checks_stock_and_policy_separately():
    answer = (
        "Product 999 is in stock. The Returns policy allows unused items "
        "to be returned within 30 days of delivery."
    )

    assert missing_checks(answer, CASES[2][1]) == ["missing product acknowledged"]


def test_evaluation_saves_pass_and_review_cases(tmp_path, monkeypatch):
    returns = "The Returns policy allows unused items within 30 days of delivery."
    replies = iter(
        [
            f"Product 123 has 15 units available. {returns}",
            "Product 123 has 15 units available. Gift-wrapping costs EUR 5.",
            f"Product 999 could not be found. {returns}",
        ]
    )
    monkeypatch.setattr(
        "evaluate_chat_tools.stream_gemini", lambda question, history: iter([next(replies)])
    )
    output = tmp_path / "baseline.json"

    assert evaluate(output) == 2

    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["passed"] == 2
    assert report["total"] == 3
    assert [case["question"] for case in report["cases"]] == [
        question for question, _ in CASES
    ]
    assert report["cases"][0]["missing_checks"] == []
    assert report["cases"][1]["missing_checks"] == ["missing policy acknowledged"]
    assert "Gift-wrapping costs EUR 5." in report["cases"][1]["answer"]
    assert report["cases"][1]["elapsed_seconds"] >= 0


def test_review_mode_compares_the_draft_and_revised_answer(monkeypatch, capsys, tmp_path):
    question, checks = CASES[1]
    monkeypatch.setattr("evaluate_chat_tools.CASES", [(question, checks)])
    evidence = [
        {"name": "get_product", "result": {"stock": 15}},
        {"name": "lookup_store_policy", "result": {"error": "No matching store policy found."}},
    ]
    draft = "Product 123 has 15 units available. Gift-wrapping costs EUR 5."
    revised = "Product 123 has 15 units available. I could not verify the gift-wrapping policy."

    def draft_stream(question, history, *, tool_results):
        tool_results.extend(evidence)
        yield draft

    reviewer = Mock(return_value=revised)
    monkeypatch.setattr("evaluate_chat_tools.stream_gemini", draft_stream)
    monkeypatch.setattr("evaluate_chat_tools.review_chat_answer", reviewer)
    monkeypatch.setattr(
        "evaluate_chat_tools.perf_counter", iter([10.0, 11.25, 12.0]).__next__
    )
    output = tmp_path / "review.json"

    assert evaluate(output, review=True) == 1
    reviewer.assert_called_once_with(question, draft, evidence)
    console = capsys.readouterr().out
    assert revised in console
    assert "Draft: REVIEW (1.25 s). Reviewer added 0.75 s." in console

    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["draft_passed"] == 0
    assert report["passed"] == 1
    case = report["cases"][0]
    assert case["draft"] == {
        "answer": draft,
        "elapsed_seconds": 1.25,
        "missing_checks": ["missing policy acknowledged"],
    }
    assert case["answer"] == revised
    assert case["missing_checks"] == []
    assert case["elapsed_seconds"] == 2.0
    assert case["review_seconds"] == 0.75
    assert case["tool_results"] == evidence
