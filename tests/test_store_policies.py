from store_policies import retrieve_policy


def test_retrieval_returns_the_policy_source_and_passage():
    result = retrieve_policy("Can I RETURN, please?")

    assert result == {
        "source": "Returns policy",
        "text": "Customers can return unused items within 30 days of delivery.",
    }


def test_retrieval_prefers_the_policy_with_more_keyword_matches():
    result = retrieve_policy("When does shipping arrive after a return?")

    assert result["source"] == "Shipping policy"


def test_retrieval_returns_none_for_an_unrelated_question():
    assert retrieve_policy("What is Python?") is None
