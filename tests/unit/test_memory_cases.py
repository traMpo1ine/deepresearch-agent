from deepresearch_agent.memory_cases import (
    get_memory_case,
    inspect_memory_case,
    load_memory_cases,
)


def test_load_memory_cases_reads_learning_examples() -> None:
    cases = load_memory_cases()

    assert {case.id for case in cases} == {
        "sqlite_vector_recall",
        "hybrid_memory_recall",
    }


def test_sqlite_vector_recall_case_links_vector_hit_back_to_sqlite_record() -> None:
    payload = inspect_memory_case(get_memory_case("sqlite_vector_recall"))

    assert payload["top_match_ok"]
    assert payload["observed_top_id"] == "ev_memory_citation"
    assert payload["vector_hits"][0]["record"]["quote"] == (
        "SQLite memory stores evidence records with source chunks and quotes."
    )


def test_hybrid_memory_case_shows_vector_id_then_sqlite_record() -> None:
    payload = inspect_memory_case(get_memory_case("hybrid_memory_recall"))

    assert payload["top_match_ok"]
    assert payload["observed_top_id"] == "ev_hybrid_vector"
    assert payload["vector_hits"][0]["record"]["source_id"] == "vector_memory"
    assert payload["sqlite_record_count"] == payload["vector_index_count"]
