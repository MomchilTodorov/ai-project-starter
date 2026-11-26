import re
from time import perf_counter

from ai_client import stream_gemini


STOCK = r"\b15\s+(?:units?|items?|available)\b"
RETURNS = (
    r"\breturns policy\b",
    r"\b(?:30|thirty)\s+days\b",
    r"\b(?:unused|not been used)\b",
    r"\bdelivery\b",
)
POLICY_MISSING = (
    r"\b(?:unable to verify|could not find|couldn't find|"
    r"cannot confirm|can't confirm|no matching (?:store )?policy)\b"
)
PRODUCT_MISSING = (
    r"\b(?:not (?:be )?found|unable to find|could not find|couldn't find|"
    r"no matching product)\b"
)

CASES = [
    (
        "Is product 123 in stock, and can I return it if I don't use it?",
        (STOCK, *RETURNS),
    ),
    (
        "Is product 123 in stock, and what is your gift-wrapping policy?",
        (STOCK, r"\bgift[- ]wrapping\b", POLICY_MISSING),
    ),
    (
        "Is product 999 in stock, and can I return an unused item?",
        (r"\b999\b", PRODUCT_MISSING, *RETURNS),
    ),
]


def evaluate():
    passed_count = 0

    for question, checks in CASES:
        started = perf_counter()
        answer = "".join(stream_gemini(question, []))
        elapsed = perf_counter() - started

        normalized = answer.casefold().replace("\u2019", "'")
        passed = all(re.search(check, normalized) for check in checks)
        passed_count += int(passed)

        status = "PASS" if passed else "REVIEW"
        print(f"{status}  {question} ({elapsed:.2f} s)")
        print(f"  {answer}\n")

    print(f"Passed {passed_count}/{len(CASES)} checks.")
    return passed_count


if __name__ == "__main__":
    evaluate()
