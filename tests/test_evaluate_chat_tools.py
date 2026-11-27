import pytest

from evaluate_chat_tools import CASES, missing_checks


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
