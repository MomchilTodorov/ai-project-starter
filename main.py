import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import re


def tokenize(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text.casefold())


def classify(ticket: str, examples: list[dict[str, str]]) -> str | None:
    """Predict a ticket category with multinomial naive Bayes."""
    example_counts: Counter[str] = Counter()
    word_counts: dict[str, Counter[str]] = defaultdict(Counter)
    vocabulary: set[str] = set()

    for example in examples:
        category = example["category"]
        words = tokenize(example["text"])
        example_counts[category] += 1
        word_counts[category].update(words)
        vocabulary.update(words)

    ticket_words = [word for word in tokenize(ticket) if word in vocabulary]
    if not ticket_words:
        return None

    scores: dict[str, float] = {}
    for category, counts in word_counts.items():
        # Add one to each word count so an unseen word does not rule out a category.
        smoothed_total = counts.total() + len(vocabulary)
        score = math.log(example_counts[category] / len(examples))
        for word in ticket_words:
            score += math.log((counts[word] + 1) / smoothed_total)
        scores[category] = score

    return max(scores, key=scores.__getitem__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Predict a support ticket category.")
    parser.add_argument("ticket", help="Support ticket text. Wrap it in quotes.")
    args = parser.parse_args()

    examples_path = Path(__file__).with_name("examples.json")
    examples = json.loads(examples_path.read_text(encoding="utf-8"))
    print(classify(args.ticket, examples) or "unknown")


if __name__ == "__main__":
    main()
