import re


# Sample policies for this exercise.
POLICIES = [
    {
        "source": "Returns policy",
        "text": "Customers can return unused items within 30 days of delivery.",
        "keywords": {"return", "returns", "refund", "refunds"},
    },
    {
        "source": "Shipping policy",
        "text": "Standard delivery takes 3 to 5 business days.",
        "keywords": {"shipping", "delivery", "arrive"},
    },
]


def retrieve_policy(question: str) -> dict[str, str] | None:
    question_words = set(re.findall(r"\b\w+\b", question.casefold()))
    best_match = None
    best_score = 0

    for policy in POLICIES:
        score = len(question_words.intersection(policy["keywords"]))

        if score > best_score:
            best_score = score
            best_match = {
                "source": policy["source"],
                "text": policy["text"],
            }

    return best_match