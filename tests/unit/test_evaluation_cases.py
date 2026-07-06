from deepresearch_agent.evaluation_cases import (
    get_evaluation_example_set,
    inspect_evaluation_case,
    load_evaluation_example_sets,
)


def test_load_evaluation_example_sets_reads_fixed_case() -> None:
    examples = load_evaluation_example_sets()

    assert set(examples) == {"baseline_vs_redblue"}
    assert len(examples["baseline_vs_redblue"].baseline) == 3
    assert len(examples["baseline_vs_redblue"].improved) == 3


def test_evaluation_case_shows_improvement_over_baseline() -> None:
    payload = inspect_evaluation_case(get_evaluation_example_set("baseline_vs_redblue"), bootstrap_samples=100)

    assert payload["improved"]["judge_score_mean"] > payload["baseline"]["judge_score_mean"]
    assert payload["delta"]["weak_support_rate"] < 0
    assert payload["delta"]["atomic_support_rate"] > 0
    assert payload["improved"]["cohens_d"] > 0
    assert len(payload["improved"]["judge_score_bootstrap_95_ci"]) == 2


def test_evaluation_case_contains_per_category_summary() -> None:
    payload = inspect_evaluation_case(get_evaluation_example_set("baseline_vs_redblue"), bootstrap_samples=100)

    assert "technical_comparison" in payload["improved"]["per_category"]
    assert "risk_analysis" in payload["improved"]["per_category"]
