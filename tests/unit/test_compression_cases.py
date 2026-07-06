from deepresearch_agent.compression_cases import (
    get_compression_case,
    inspect_compression_case,
    load_compression_cases,
)


def test_load_compression_cases_reads_learning_examples() -> None:
    cases = load_compression_cases()

    assert {case.id for case in cases} == {
        "quote_preservation",
        "multi_quote_preservation",
        "salience_filter",
    }


def test_quote_preservation_case_keeps_cited_quote() -> None:
    _context, payload = inspect_compression_case(get_compression_case("quote_preservation"))

    assert payload["preserved_quote_count"] == 1
    assert payload["all_quotes_preserved"]
    assert any(sentence["preserved_quote"] for sentence in payload["selected_sentences"])


def test_multi_quote_case_keeps_all_cited_quotes_even_with_small_max_sentences() -> None:
    context, payload = inspect_compression_case(get_compression_case("multi_quote_preservation"))

    assert payload["preserved_quote_count"] == 2
    assert payload["all_quotes_preserved"]
    assert len(context.sentences) >= 2


def test_salience_filter_case_compresses_without_quotes() -> None:
    _context, payload = inspect_compression_case(get_compression_case("salience_filter"))

    assert payload["expected_quote_count"] == 0
    assert payload["preserved_quote_count"] == 0
    assert payload["compression_ratio"] < 1.0
    assert len(payload["selected_sentences"]) <= 2
