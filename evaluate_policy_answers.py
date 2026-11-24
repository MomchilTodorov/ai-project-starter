import re

from policy_demo import answer_policy_question


CASES = [
    (
        "Can I send an unused item back?",
        "Returns policy",
        (r"\b(?:30|thirty)\s+days\b", r"\b(?:unused|not been used)\b"),
    ),
    (
        "How soon will my package get here?",
        "Shipping policy",
        (r"\b(?:3|three)\s*(?:to|[-–—])\s*(?:5|five)\s+business\s+days\b",),
    ),
    (
        "What is Python?",
        None,
        (r"couldn't find a relevant store policy",),
    ),
]


def evaluate():
    correct = 0

    for question, expected_source, patterns in CASES:
        result = answer_policy_question(question)
        answer = result["answer"] or ""
        facts_match = all(re.search(pattern, answer, re.IGNORECASE) for pattern in patterns)
        passed = result["source"] == expected_source and facts_match

        if passed:
            correct += 1

        print(f"{'PASS' if passed else 'REVIEW'}  {question}")
        print(f"  Source: {result['source']!r} (expected {expected_source!r})")
        print(f"  Answer: {answer}\n")

    print(f"Matched {correct}/{len(CASES)} checks.")


if __name__ == "__main__":
    evaluate()