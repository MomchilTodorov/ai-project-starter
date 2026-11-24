import re


# Sample policies for this exercise.
POLICIES = [
    {
        "source": "Returns policy",
        "text": "Customers can return unused items within 30 days of delivery.",
        "keywords": {"return", "returns", "refund", "refunds"},
        "phrase_patterns": (
            r"\bsend(?: \w+){0,4} (?:item|product|order|package) back\b",
        ),
    },
    {
        "source": "Shipping policy",
        "text": "Standard delivery takes 3 to 5 business days.",
        "keywords": {"shipping", "delivery", "arrive"},
        "phrase_patterns": (
            r"\b(?:order|package)(?: \w+){0,3} get here\b",
        ),
    },
]


def retrieve_policy(question: str) -> dict[str, str] | None:
    words = re.findall(r"\b\w+\b", question.casefold())
    question_words = set(words)
    question_text = " ".join(words)
    best_match = None
    best_score = 0

    for policy in POLICIES:
        score = len(question_words.intersection(policy["keywords"]))
        score += sum(
            1 for pattern in policy["phrase_patterns"]
            if re.search(pattern, question_text)
        )

        if score > best_score:
            best_score = score
            best_match = {
                "source": policy["source"],
                "text": policy["text"],
            }

    return best_match