from store_policies import retrieve_policy


CASES = [
    ("How long do I have to return an item?", "Returns policy"),
    ("When will my delivery arrive?", "Shipping policy"),
    ("How long does standard shipping take?", "Shipping policy"),
    ("Can I send an unused item back?", "Returns policy"),
    ("How soon will my package get here?", "Shipping policy"),
    ("What is Python?", None),
]


def evaluate():
    correct = 0

    for question, expected_source in CASES:
        policy = retrieve_policy(question)
        actual_source = policy["source"] if policy is not None else None

        if actual_source == expected_source:
            correct += 1
        else:
            print(f"MISS  {question}")
            print(f"      Expected {expected_source!r}, got {actual_source!r}")

    total = len(CASES)
    print(f"\nMatched {correct}/{total} ({correct / total:.0%}).")


if __name__ == "__main__":
    evaluate()