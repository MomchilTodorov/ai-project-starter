import re
from time import perf_counter

from ai_client import stream_gemini


STOCK = ("15 units available", r"\b15\s+(?:units?|items?|available)\b")
RETURNS = (
    ("Returns policy named", r"\breturns policy\b"),
    ("30-day return window", r"\b(?:30|thirty)\s+days\b"),
    ("unused-item condition", r"\b(?:unused|not been used)\b"),
    ("window starts at delivery", r"\bdelivery\b"),
)
POLICY_MISSING = (
    "missing policy acknowledged",
    r"\b(?:(?:unable to|could not|couldn't|cannot|can't) (?:verify|find|confirm)"
    r"|no matching (?:store )?policy)\b",
)
PRODUCT_MISSING = (
    "missing product acknowledged",
    r"\b(?:not (?:be )?found|unable to find|could not find|couldn't find|"
    r"no matching product)\b",
)

CASES = [
    (
        "Is product 123 in stock, and can I return it if I don't use it?",
        (STOCK, *RETURNS),
    ),
    (
        "Is product 123 in stock, and what is your gift-wrapping policy?",
        (STOCK, ("gift wrapping mentioned", r"\bgift[- ]wrapping\b"), POLICY_MISSING),
    ),
    (
        "Is product 999 in stock, and can I return an unused item?",
        (("product 999 named", r"\b999\b"), PRODUCT_MISSING, *RETURNS),
    ),
]


def missing_checks(answer: str, checks: tuple[tuple[str, str], ...]) -> list[str]:
    normalized = answer.casefold().replace("\u2019", "'")
    return [label for label, pattern in checks if not re.search(pattern, normalized)]


def evaluate():
    passed_count = 0

    for question, checks in CASES:
        started = perf_counter()
        answer = "".join(stream_gemini(question, []))
        elapsed = perf_counter() - started

        missing = missing_checks(answer, checks)
        passed_count += int(not missing)

        status = "REVIEW" if missing else "PASS"
        print(f"{status}  {question} ({elapsed:.2f} s)")
        if missing:
            print(f"  Checks to review: {', '.join(missing)}")
        print(f"  {answer}\n")

    print(f"Passed {passed_count}/{len(CASES)} checks.")
    return passed_count


if __name__ == "__main__":
    evaluate()
