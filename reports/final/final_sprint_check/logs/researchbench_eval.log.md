$ D:\学习deepsearch\.venv\Scripts\python.exe scripts/run_eval.py --config configs/default.toml --experiments baseline,memory,compression,verifier,redblue,full --experiment-dir reports\final\final_sprint_check\researchbench --summary-markdown reports\final\final_sprint_check\researchbench_summary.md --output reports\final\final_sprint_check\researchbench_metrics.json --memory-path reports\final\final_sprint_check\memory\researchbench.sqlite3 --vector-path reports\final\final_sprint_check\memory\researchbench_vector.npz

## STDOUT
{
  "baseline": {
    "n": 35,
    "judge_score_mean": 0.7737333333333337,
    "judge_score_bootstrap_95_ci": [
      0.76,
      0.7874666666666668
    ],
    "cohens_d": 9.020102938001434,
    "factual_accuracy": 0.0,
    "hallucination_rate": 0.0,
    "weak_support_rate": 1.0,
    "citation_coverage": 1.0,
    "evidence_reuse_rate": 0.0,
    "compression_ratio": 1.0,
    "repair_success_rate": 1.0,
    "atomic_support_rate": 0.0,
    "contradiction_detection_rate": 0.0,
    "repair_precision": 0.0,
    "repair_coverage": 0.0,
    "repair_convergence_rate": 0.0,
    "repair_oscillation_rate": 0.0,
    "avg_repair_rounds": 0.0,
    "evidence_grounding_score": 1.0,
    "avg_task_latency": 0.037715523384612835,
    "per_category": {
      "factual_explanation": {
        "n": 29,
        "judge_score_mean": 0.7763448275862073,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "evidence_grounding_score": 1.0
      },
      "multi_hop_reasoning": {
        "n": 1,
        "judge_score_mean": 0.7066666666666667,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "evidence_grounding_score": 1.0
      },
      "risk_analysis": {
        "n": 2,
        "judge_score_mean": 0.8,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "evidence_grounding_score": 1.0
      },
      "technical_comparison": {
        "n": 1,
        "judge_score_mean": 0.8,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "evidence_grounding_score": 1.0
      },
      "solution_design": {
        "n": 2,
        "judge_score_mean": 0.73,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "evidence_grounding_score": 1.0
      }
    },
    "per_domain": {
      "citation_verification": {
        "n": 3,
        "judge_score_mean": 0.8000000000000002,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "agent_orchestration": {
        "n": 5,
        "judge_score_mean": 0.7346666666666668,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "memory_retrieval": {
        "n": 3,
        "judge_score_mean": 0.8000000000000002,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "context_compression": {
        "n": 2,
        "judge_score_mean": 0.7533333333333334,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "redblue_repair": {
        "n": 3,
        "judge_score_mean": 0.8000000000000002,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "evaluation": {
        "n": 5,
        "judge_score_mean": 0.7486666666666666,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "multi_hop": {
        "n": 2,
        "judge_score_mean": 0.7533333333333334,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "llm_backend": {
        "n": 3,
        "judge_score_mean": 0.8000000000000002,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "engineering_tradeoff": {
        "n": 5,
        "judge_score_mean": 0.7813333333333332,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "reliability": {
        "n": 2,
        "judge_score_mean": 0.8,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "rag_system": {
        "n": 2,
        "judge_score_mean": 0.772,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      }
    },
    "judge_score_dimensions": {
      "factuality": 0.0,
      "coverage": 0.9061904761904761,
      "citation_quality": 1.0,
      "structure": 1.0,
      "usefulness": 0.9624761904761905
    },
    "multi_hop_subset": {
      "n": 13,
      "judge_score_mean": 0.7784615384615385,
      "hallucination_rate": 0.0,
      "weak_support_rate": 1.0,
      "citation_coverage": 1.0,
      "atomic_support_rate": 0.0,
      "repair_precision": 0.0,
      "repair_coverage": 0.0
    },
    "hotpot_style_subset": {
      "n": 6,
      "judge_score_mean": 0.7688888888888888,
      "hallucination_rate": 0.0,
      "weak_support_rate": 1.0,
      "citation_coverage": 1.0,
      "atomic_support_rate": 0.0,
      "repair_precision": 0.0,
      "repair_coverage": 0.0
    },
    "repair_action_distribution": {}
  },
  "memory": {
    "n": 35,
    "judge_score_mean": 0.779066666666667,
    "judge_score_bootstrap_95_ci": [
      0.7637333333333334,
      0.792
    ],
    "cohens_d": 0.12864064075959747,
    "factual_accuracy": 0.0,
    "hallucination_rate": 0.0,
    "weak_support_rate": 1.0,
    "citation_coverage": 1.0,
    "evidence_reuse_rate": 0.35793011843432027,
    "compression_ratio": 1.0,
    "repair_success_rate": 1.0,
    "atomic_support_rate": 0.0,
    "contradiction_detection_rate": 0.0,
    "repair_precision": 0.0,
    "repair_coverage": 0.0,
    "repair_convergence_rate": 0.0,
    "repair_oscillation_rate": 0.0,
    "avg_repair_rounds": 0.0,
    "evidence_grounding_score": 1.0,
    "avg_task_latency": 0.032780876734279214,
    "per_category": {
      "factual_explanation": {
        "n": 29,
        "judge_score_mean": 0.7827816091954026,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "evidence_grounding_score": 1.0
      },
      "multi_hop_reasoning": {
        "n": 1,
        "judge_score_mean": 0.7066666666666667,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "evidence_grounding_score": 1.0
      },
      "risk_analysis": {
        "n": 2,
        "judge_score_mean": 0.8,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "evidence_grounding_score": 1.0
      },
      "technical_comparison": {
        "n": 1,
        "judge_score_mean": 0.8,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "evidence_grounding_score": 1.0
      },
      "solution_design": {
        "n": 2,
        "judge_score_mean": 0.73,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "evidence_grounding_score": 1.0
      }
    },
    "per_domain": {
      "citation_verification": {
        "n": 3,
        "judge_score_mean": 0.8000000000000002,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "agent_orchestration": {
        "n": 5,
        "judge_score_mean": 0.7346666666666668,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "memory_retrieval": {
        "n": 3,
        "judge_score_mean": 0.8000000000000002,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "context_compression": {
        "n": 2,
        "judge_score_mean": 0.7533333333333334,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "redblue_repair": {
        "n": 3,
        "judge_score_mean": 0.8000000000000002,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "evaluation": {
        "n": 5,
        "judge_score_mean": 0.7673333333333334,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "multi_hop": {
        "n": 2,
        "judge_score_mean": 0.7533333333333334,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "llm_backend": {
        "n": 3,
        "judge_score_mean": 0.8000000000000002,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "engineering_tradeoff": {
        "n": 5,
        "judge_score_mean": 0.8,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "reliability": {
        "n": 2,
        "judge_score_mean": 0.8,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "rag_system": {
        "n": 2,
        "judge_score_mean": 0.772,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      }
    },
    "judge_score_dimensions": {
      "factuality": 0.0,
      "coverage": 0.9252380952380952,
      "citation_quality": 1.0,
      "structure": 1.0,
      "usefulness": 0.9700952380952381
    },
    "multi_hop_subset": {
      "n": 13,
      "judge_score_mean": 0.7784615384615385,
      "hallucination_rate": 0.0,
      "weak_support_rate": 1.0,
      "citation_coverage": 1.0,
      "atomic_support_rate": 0.0,
      "repair_precision": 0.0,
      "repair_coverage": 0.0
    },
    "hotpot_style_subset": {
      "n": 6,
      "judge_score_mean": 0.7688888888888888,
      "hallucination_rate": 0.0,
      "weak_support_rate": 1.0,
      "citation_coverage": 1.0,
      "atomic_support_rate": 0.0,
      "repair_precision": 0.0,
      "repair_coverage": 0.0
    },
    "repair_action_distribution": {}
  },
  "compression": {
    "n": 35,
    "judge_score_mean": 0.779066666666667,
    "judge_score_bootstrap_95_ci": [
      0.766,
      0.7914666666666667
    ],
    "cohens_d": 0.12864064075959747,
    "factual_accuracy": 0.0,
    "hallucination_rate": 0.0,
    "weak_support_rate": 1.0,
    "citation_coverage": 1.0,
    "evidence_reuse_rate": 0.35793011843432027,
    "compression_ratio": 0.44468747204147885,
    "repair_success_rate": 1.0,
    "atomic_support_rate": 0.0,
    "contradiction_detection_rate": 0.0,
    "repair_precision": 0.0,
    "repair_coverage": 0.0,
    "repair_convergence_rate": 0.0,
    "repair_oscillation_rate": 0.0,
    "avg_repair_rounds": 0.0,
    "evidence_grounding_score": 1.0,
    "avg_task_latency": 0.03259839181410246,
    "per_category": {
      "factual_explanation": {
        "n": 29,
        "judge_score_mean": 0.7827816091954026,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "evidence_grounding_score": 1.0
      },
      "multi_hop_reasoning": {
        "n": 1,
        "judge_score_mean": 0.7066666666666667,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "evidence_grounding_score": 1.0
      },
      "risk_analysis": {
        "n": 2,
        "judge_score_mean": 0.8,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "evidence_grounding_score": 1.0
      },
      "technical_comparison": {
        "n": 1,
        "judge_score_mean": 0.8,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "evidence_grounding_score": 1.0
      },
      "solution_design": {
        "n": 2,
        "judge_score_mean": 0.73,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "evidence_grounding_score": 1.0
      }
    },
    "per_domain": {
      "citation_verification": {
        "n": 3,
        "judge_score_mean": 0.8000000000000002,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "agent_orchestration": {
        "n": 5,
        "judge_score_mean": 0.7346666666666668,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "memory_retrieval": {
        "n": 3,
        "judge_score_mean": 0.8000000000000002,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "context_compression": {
        "n": 2,
        "judge_score_mean": 0.7533333333333334,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "redblue_repair": {
        "n": 3,
        "judge_score_mean": 0.8000000000000002,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "evaluation": {
        "n": 5,
        "judge_score_mean": 0.7673333333333334,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "multi_hop": {
        "n": 2,
        "judge_score_mean": 0.7533333333333334,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "llm_backend": {
        "n": 3,
        "judge_score_mean": 0.8000000000000002,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "engineering_tradeoff": {
        "n": 5,
        "judge_score_mean": 0.8,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "reliability": {
        "n": 2,
        "judge_score_mean": 0.8,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "rag_system": {
        "n": 2,
        "judge_score_mean": 0.772,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      }
    },
    "judge_score_dimensions": {
      "factuality": 0.0,
      "coverage": 0.9252380952380952,
      "citation_quality": 1.0,
      "structure": 1.0,
      "usefulness": 0.9700952380952381
    },
    "multi_hop_subset": {
      "n": 13,
      "judge_score_mean": 0.7784615384615385,
      "hallucination_rate": 0.0,
      "weak_support_rate": 1.0,
      "citation_coverage": 1.0,
      "atomic_support_rate": 0.0,
      "repair_precision": 0.0,
      "repair_coverage": 0.0
    },
    "hotpot_style_subset": {
      "n": 6,
      "judge_score_mean": 0.7688888888888888,
      "hallucination_rate": 0.0,
      "weak_support_rate": 1.0,
      "citation_coverage": 1.0,
      "atomic_support_rate": 0.0,
      "repair_precision": 0.0,
      "repair_coverage": 0.0
    },
    "repair_action_distribution": {}
  },
  "verifier": {
    "n": 35,
    "judge_score_mean": 0.8666857142857145,
    "judge_score_bootstrap_95_ci": [
      0.8462095238095239,
      0.8866857142857144
    ],
    "cohens_d": 1.7601720104646963,
    "factual_accuracy": 0.9047619047619048,
    "hallucination_rate": 0.09523809523809526,
    "weak_support_rate": 0.6571428571428573,
    "citation_coverage": 1.0,
    "evidence_reuse_rate": 0.35793011843432027,
    "compression_ratio": 0.44468747204147885,
    "repair_success_rate": 1.0,
    "atomic_support_rate": 0.47074829931972795,
    "contradiction_detection_rate": 0.0,
    "repair_precision": 0.0,
    "repair_coverage": 0.0,
    "repair_convergence_rate": 1.0,
    "repair_oscillation_rate": 0.0,
    "avg_repair_rounds": 1.0,
    "evidence_grounding_score": 0.26862244897959187,
    "avg_task_latency": 0.0290315424373253,
    "per_category": {
      "factual_explanation": {
        "n": 29,
        "judge_score_mean": 0.8655402298850576,
        "hallucination_rate": 0.09195402298850575,
        "weak_support_rate": 0.6781609195402298,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.4384236453201971,
        "evidence_grounding_score": 0.25685207991242476
      },
      "multi_hop_reasoning": {
        "n": 1,
        "judge_score_mean": 0.7733333333333333,
        "hallucination_rate": 0.6666666666666666,
        "weak_support_rate": 1.3333333333333333,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.2857142857142857,
        "evidence_grounding_score": 0.10714285714285714
      },
      "risk_analysis": {
        "n": 2,
        "judge_score_mean": 0.9000000000000001,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.5,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.5952380952380952,
        "evidence_grounding_score": 0.3070436507936508
      },
      "technical_comparison": {
        "n": 1,
        "judge_score_mean": 1.0,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 1.0,
        "evidence_grounding_score": 0.6842261904761905
      },
      "solution_design": {
        "n": 2,
        "judge_score_mean": 0.8300000000000001,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.5,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.6428571428571428,
        "evidence_grounding_score": 0.27380952380952384
      }
    },
    "per_domain": {
      "citation_verification": {
        "n": 3,
        "judge_score_mean": 0.888888888888889,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.5555555555555555,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.48412698412698413,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "agent_orchestration": {
        "n": 5,
        "judge_score_mean": 0.8013333333333333,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.6666666666666666,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.48571428571428565,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "memory_retrieval": {
        "n": 3,
        "judge_score_mean": 0.8444444444444446,
        "hallucination_rate": 0.1111111111111111,
        "weak_support_rate": 0.8888888888888888,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.28571428571428564,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "context_compression": {
        "n": 2,
        "judge_score_mean": 0.8200000000000001,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.6666666666666666,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.30952380952380953,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "redblue_repair": {
        "n": 3,
        "judge_score_mean": 0.888888888888889,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.5555555555555555,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.5476190476190476,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "evaluation": {
        "n": 5,
        "judge_score_mean": 0.874,
        "hallucination_rate": 0.2,
        "weak_support_rate": 0.6666666666666666,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.5142857142857142,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "multi_hop": {
        "n": 2,
        "judge_score_mean": 0.8866666666666667,
        "hallucination_rate": 0.3333333333333333,
        "weak_support_rate": 0.6666666666666666,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.6428571428571428,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "llm_backend": {
        "n": 3,
        "judge_score_mean": 0.8666666666666668,
        "hallucination_rate": 0.1111111111111111,
        "weak_support_rate": 0.7777777777777777,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.2857142857142857,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "engineering_tradeoff": {
        "n": 5,
        "judge_score_mean": 0.9066666666666668,
        "hallucination_rate": 0.2,
        "weak_support_rate": 0.6666666666666666,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.5428571428571428,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "reliability": {
        "n": 2,
        "judge_score_mean": 0.9000000000000001,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.5,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.45238095238095233,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "rag_system": {
        "n": 2,
        "judge_score_mean": 0.8720000000000001,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.5,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.5714285714285714,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      }
    },
    "judge_score_dimensions": {
      "factuality": 0.43809523809523826,
      "coverage": 0.9252380952380952,
      "citation_quality": 1.0,
      "structure": 1.0,
      "usefulness": 0.9700952380952381
    },
    "multi_hop_subset": {
      "n": 13,
      "judge_score_mean": 0.8758974358974361,
      "hallucination_rate": 0.07692307692307693,
      "weak_support_rate": 0.5897435897435898,
      "citation_coverage": 1.0,
      "atomic_support_rate": 0.5091575091575091,
      "repair_precision": 0.0,
      "repair_coverage": 0.0
    },
    "hotpot_style_subset": {
      "n": 6,
      "judge_score_mean": 0.8577777777777778,
      "hallucination_rate": 0.1111111111111111,
      "weak_support_rate": 0.6666666666666666,
      "citation_coverage": 1.0,
      "atomic_support_rate": 0.5079365079365079,
      "repair_precision": 0.0,
      "repair_coverage": 0.0
    },
    "repair_action_distribution": {}
  },
  "redblue": {
    "n": 35,
    "judge_score_mean": 0.8800190476190477,
    "judge_score_bootstrap_95_ci": [
      0.8590476190476191,
      0.9006666666666667
    ],
    "cohens_d": 1.916935713751418,
    "factual_accuracy": 1.0,
    "hallucination_rate": 0.0,
    "weak_support_rate": 0.4952380952380951,
    "citation_coverage": 1.0,
    "evidence_reuse_rate": 0.35793011843432027,
    "compression_ratio": 0.44468747204147885,
    "repair_success_rate": 1.0,
    "atomic_support_rate": 0.6097278911564625,
    "contradiction_detection_rate": 0.0,
    "repair_precision": 0.8952380952380953,
    "repair_coverage": 1.0,
    "repair_convergence_rate": 1.0,
    "repair_oscillation_rate": 0.4857142857142857,
    "avg_repair_rounds": 1.9714285714285715,
    "evidence_grounding_score": 0.31210317460317466,
    "avg_task_latency": 0.023158797071242188,
    "per_category": {
      "factual_explanation": {
        "n": 29,
        "judge_score_mean": 0.8770344827586207,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.528735632183908,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.5864532019704434,
        "evidence_grounding_score": 0.3010775862068965
      },
      "multi_hop_reasoning": {
        "n": 1,
        "judge_score_mean": 0.9066666666666666,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 1.0,
        "evidence_grounding_score": 0.375
      },
      "risk_analysis": {
        "n": 2,
        "judge_score_mean": 0.9000000000000001,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.5,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.5238095238095238,
        "evidence_grounding_score": 0.2912698412698413
      },
      "technical_comparison": {
        "n": 1,
        "judge_score_mean": 1.0,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 1.0,
        "evidence_grounding_score": 0.6842261904761905
      },
      "solution_design": {
        "n": 2,
        "judge_score_mean": 0.8300000000000001,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.5,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.6428571428571428,
        "evidence_grounding_score": 0.27529761904761907
      }
    },
    "per_domain": {
      "citation_verification": {
        "n": 3,
        "judge_score_mean": 0.888888888888889,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.5555555555555555,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.5317460317460317,
        "repair_precision": 1.0,
        "repair_coverage": 1.0
      },
      "agent_orchestration": {
        "n": 5,
        "judge_score_mean": 0.8013333333333333,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.6666666666666666,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.5142857142857142,
        "repair_precision": 1.0,
        "repair_coverage": 1.0
      },
      "memory_retrieval": {
        "n": 3,
        "judge_score_mean": 0.8555555555555556,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.7222222222222222,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.44047619047619047,
        "repair_precision": 0.8888888888888888,
        "repair_coverage": 1.0
      },
      "context_compression": {
        "n": 2,
        "judge_score_mean": 0.8200000000000001,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.6666666666666666,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.38095238095238093,
        "repair_precision": 1.0,
        "repair_coverage": 1.0
      },
      "redblue_repair": {
        "n": 3,
        "judge_score_mean": 0.888888888888889,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.5555555555555555,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.5476190476190477,
        "repair_precision": 1.0,
        "repair_coverage": 1.0
      },
      "evaluation": {
        "n": 5,
        "judge_score_mean": 0.9006666666666666,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.3333333333333333,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.7857142857142857,
        "repair_precision": 0.7666666666666666,
        "repair_coverage": 1.0
      },
      "multi_hop": {
        "n": 2,
        "judge_score_mean": 0.9533333333333334,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 1.0,
        "repair_precision": 0.6666666666666666,
        "repair_coverage": 1.0
      },
      "llm_backend": {
        "n": 3,
        "judge_score_mean": 0.8777777777777779,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.611111111111111,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.41904761904761906,
        "repair_precision": 0.8888888888888888,
        "repair_coverage": 1.0
      },
      "engineering_tradeoff": {
        "n": 5,
        "judge_score_mean": 0.9333333333333333,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.3333333333333333,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.8142857142857143,
        "repair_precision": 0.7666666666666666,
        "repair_coverage": 1.0
      },
      "reliability": {
        "n": 2,
        "judge_score_mean": 0.9000000000000001,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.5,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.45238095238095233,
        "repair_precision": 1.0,
        "repair_coverage": 1.0
      },
      "rag_system": {
        "n": 2,
        "judge_score_mean": 0.8720000000000001,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.5,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.6428571428571428,
        "repair_precision": 1.0,
        "repair_coverage": 1.0
      }
    },
    "judge_score_dimensions": {
      "factuality": 0.5047619047619049,
      "coverage": 0.9252380952380952,
      "citation_quality": 1.0,
      "structure": 1.0,
      "usefulness": 0.9700952380952381
    },
    "multi_hop_subset": {
      "n": 13,
      "judge_score_mean": 0.8887179487179488,
      "hallucination_rate": 0.0,
      "weak_support_rate": 0.4487179487179487,
      "citation_coverage": 1.0,
      "atomic_support_rate": 0.6058608058608059,
      "repair_precision": 0.9230769230769229,
      "repair_coverage": 1.0
    },
    "hotpot_style_subset": {
      "n": 6,
      "judge_score_mean": 0.88,
      "hallucination_rate": 0.0,
      "weak_support_rate": 0.4444444444444444,
      "citation_coverage": 1.0,
      "atomic_support_rate": 0.626984126984127,
      "repair_precision": 0.8888888888888888,
      "repair_coverage": 1.0
    },
    "repair_action_distribution": {
      "modify": 49,
      "delete": 10,
      "add": 17
    }
  },
  "full": {
    "n": 35,
    "judge_score_mean": 0.8800190476190477,
    "judge_score_bootstrap_95_ci": [
      0.8581904761904763,
      0.9031619047619048
    ],
    "cohens_d": 1.916935713751418,
    "factual_accuracy": 1.0,
    "hallucination_rate": 0.0,
    "weak_support_rate": 0.4952380952380951,
    "citation_coverage": 1.0,
    "evidence_reuse_rate": 0.35793011843432027,
    "compression_ratio": 0.44468747204147885,
    "repair_success_rate": 1.0,
    "atomic_support_rate": 0.6097278911564625,
    "contradiction_detection_rate": 0.0,
    "repair_precision": 0.8952380952380953,
    "repair_coverage": 1.0,
    "repair_convergence_rate": 1.0,
    "repair_oscillation_rate": 0.4857142857142857,
    "avg_repair_rounds": 1.9714285714285715,
    "evidence_grounding_score": 0.31210317460317466,
    "avg_task_latency": 0.023164764942872486,
    "per_category": {
      "factual_explanation": {
        "n": 29,
        "judge_score_mean": 0.8770344827586207,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.528735632183908,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.5864532019704434,
        "evidence_grounding_score": 0.3010775862068965
      },
      "multi_hop_reasoning": {
        "n": 1,
        "judge_score_mean": 0.9066666666666666,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 1.0,
        "evidence_grounding_score": 0.375
      },
      "risk_analysis": {
        "n": 2,
        "judge_score_mean": 0.9000000000000001,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.5,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.5238095238095238,
        "evidence_grounding_score": 0.2912698412698413
      },
      "technical_comparison": {
        "n": 1,
        "judge_score_mean": 1.0,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 1.0,
        "evidence_grounding_score": 0.6842261904761905
      },
      "solution_design": {
        "n": 2,
        "judge_score_mean": 0.8300000000000001,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.5,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.6428571428571428,
        "evidence_grounding_score": 0.27529761904761907
      }
    },
    "per_domain": {
      "citation_verification": {
        "n": 3,
        "judge_score_mean": 0.888888888888889,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.5555555555555555,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.5317460317460317,
        "repair_precision": 1.0,
        "repair_coverage": 1.0
      },
      "agent_orchestration": {
        "n": 5,
        "judge_score_mean": 0.8013333333333333,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.6666666666666666,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.5142857142857142,
        "repair_precision": 1.0,
        "repair_coverage": 1.0
      },
      "memory_retrieval": {
        "n": 3,
        "judge_score_mean": 0.8555555555555556,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.7222222222222222,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.44047619047619047,
        "repair_precision": 0.8888888888888888,
        "repair_coverage": 1.0
      },
      "context_compression": {
        "n": 2,
        "judge_score_mean": 0.8200000000000001,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.6666666666666666,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.38095238095238093,
        "repair_precision": 1.0,
        "repair_coverage": 1.0
      },
      "redblue_repair": {
        "n": 3,
        "judge_score_mean": 0.888888888888889,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.5555555555555555,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.5476190476190477,
        "repair_precision": 1.0,
        "repair_coverage": 1.0
      },
      "evaluation": {
        "n": 5,
        "judge_score_mean": 0.9006666666666666,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.3333333333333333,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.7857142857142857,
        "repair_precision": 0.7666666666666666,
        "repair_coverage": 1.0
      },
      "multi_hop": {
        "n": 2,
        "judge_score_mean": 0.9533333333333334,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 1.0,
        "repair_precision": 0.6666666666666666,
        "repair_coverage": 1.0
      },
      "llm_backend": {
        "n": 3,
        "judge_score_mean": 0.8777777777777779,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.611111111111111,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.41904761904761906,
        "repair_precision": 0.8888888888888888,
        "repair_coverage": 1.0
      },
      "engineering_tradeoff": {
        "n": 5,
        "judge_score_mean": 0.9333333333333333,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.3333333333333333,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.8142857142857143,
        "repair_precision": 0.7666666666666666,
        "repair_coverage": 1.0
      },
      "reliability": {
        "n": 2,
        "judge_score_mean": 0.9000000000000001,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.5,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.45238095238095233,
        "repair_precision": 1.0,
        "repair_coverage": 1.0
      },
      "rag_system": {
        "n": 2,
        "judge_score_mean": 0.8720000000000001,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.5,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.6428571428571428,
        "repair_precision": 1.0,
        "repair_coverage": 1.0
      }
    },
    "judge_score_dimensions": {
      "factuality": 0.5047619047619049,
      "coverage": 0.9252380952380952,
      "citation_quality": 1.0,
      "structure": 1.0,
      "usefulness": 0.9700952380952381
    },
    "multi_hop_subset": {
      "n": 13,
      "judge_score_mean": 0.8887179487179488,
      "hallucination_rate": 0.0,
      "weak_support_rate": 0.4487179487179487,
      "citation_coverage": 1.0,
      "atomic_support_rate": 0.6058608058608059,
      "repair_precision": 0.9230769230769229,
      "repair_coverage": 1.0
    },
    "hotpot_style_subset": {
      "n": 6,
      "judge_score_mean": 0.88,
      "hallucination_rate": 0.0,
      "weak_support_rate": 0.4444444444444444,
      "citation_coverage": 1.0,
      "atomic_support_rate": 0.626984126984127,
      "repair_precision": 0.8888888888888888,
      "repair_coverage": 1.0
    },
    "repair_action_distribution": {
      "modify": 49,
      "delete": 10,
      "add": 17
    }
  }
}


## STDERR


Exit code: 0