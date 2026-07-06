from deepresearch_agent.evaluation.runner import load_benchmark, summarize_dataset_file


def test_extended_researchbench_has_resume_ready_coverage() -> None:
    summary = summarize_dataset_file(
        "data/benchmarks/researchbench_extended.jsonl",
        "researchbench_extended",
    )

    assert 60 <= summary["case_count"] <= 80
    assert all(count >= 7 for count in summary["answer_type_counts"].values())
    assert summary["multi_hop_count"] >= 10
    assert summary["hotpot_style_count"] >= 10


def test_extended_researchbench_loads_with_answer_types() -> None:
    cases = load_benchmark("data/benchmarks/researchbench_extended.jsonl")
    answer_types = {case.answer_type for case in cases}

    assert len(cases) == 60
    assert answer_types == {
        "factual_explanation",
        "multi_hop_reasoning",
        "risk_analysis",
        "technical_comparison",
        "solution_design",
    }
