$ D:\学习deepsearch\.venv\Scripts\python.exe scripts/run_eval.py --suite adversarial --experiments baseline,verifier,redblue --experiment-dir reports\final\final_sprint_check\adversarial --summary-markdown reports\final\final_sprint_check\adversarial_summary.md --output reports\final\final_sprint_check\adversarial_metrics.json --memory-path reports\final\final_sprint_check\memory\adversarial.sqlite3 --vector-path reports\final\final_sprint_check\memory\adversarial_vector.npz

## STDOUT
{
  "baseline": {
    "n": 10,
    "judge_score_mean": 0.7906666666666665,
    "judge_score_bootstrap_95_ci": [
      0.772,
      0.8
    ],
    "cohens_d": 14.680883647492125,
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
    "avg_task_latency": 0.03702194571628102,
    "per_category": {
      "risk_analysis": {
        "n": 5,
        "judge_score_mean": 0.7813333333333332,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "evidence_grounding_score": 1.0
      },
      "factual_explanation": {
        "n": 1,
        "judge_score_mean": 0.8,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "evidence_grounding_score": 1.0
      },
      "technical_comparison": {
        "n": 3,
        "judge_score_mean": 0.8000000000000002,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "evidence_grounding_score": 1.0
      },
      "solution_design": {
        "n": 1,
        "judge_score_mean": 0.8,
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
      "context_compression": {
        "n": 1,
        "judge_score_mean": 0.7066666666666667,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "redblue_repair": {
        "n": 1,
        "judge_score_mean": 0.8,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "engineering_tradeoff": {
        "n": 3,
        "judge_score_mean": 0.8000000000000002,
        "hallucination_rate": 0.0,
        "weak_support_rate": 1.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.0,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "memory_retrieval": {
        "n": 2,
        "judge_score_mean": 0.8,
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
      "coverage": 0.9666666666666666,
      "citation_quality": 1.0,
      "structure": 1.0,
      "usefulness": 0.9866666666666667
    },
    "multi_hop_subset": {
      "n": 7,
      "judge_score_mean": 0.7866666666666665,
      "hallucination_rate": 0.0,
      "weak_support_rate": 1.0,
      "citation_coverage": 1.0,
      "atomic_support_rate": 0.0,
      "repair_precision": 0.0,
      "repair_coverage": 0.0
    },
    "hotpot_style_subset": {
      "n": 0,
      "judge_score_mean": 0.0,
      "hallucination_rate": 0.0,
      "weak_support_rate": 0.0,
      "citation_coverage": 0.0,
      "atomic_support_rate": 0.0,
      "repair_precision": 0.0,
      "repair_coverage": 0.0
    },
    "repair_action_distribution": {}
  },
  "verifier": {
    "n": 10,
    "judge_score_mean": 0.9066666666666668,
    "judge_score_bootstrap_95_ci": [
      0.8800000000000001,
      0.9333333333333333
    ],
    "cohens_d": 3.1342449233355896,
    "factual_accuracy": 0.8999999999999998,
    "hallucination_rate": 0.1,
    "weak_support_rate": 0.5666666666666667,
    "citation_coverage": 1.0,
    "evidence_reuse_rate": 0.2966126194067371,
    "compression_ratio": 0.43842035416620256,
    "repair_success_rate": 1.0,
    "atomic_support_rate": 0.6285714285714284,
    "contradiction_detection_rate": 0.0,
    "repair_precision": 0.0,
    "repair_coverage": 0.0,
    "repair_convergence_rate": 1.0,
    "repair_oscillation_rate": 0.0,
    "avg_repair_rounds": 1.0,
    "evidence_grounding_score": 0.33694444444444444,
    "avg_task_latency": 0.024551780007979168,
    "per_category": {
      "risk_analysis": {
        "n": 5,
        "judge_score_mean": 0.8933333333333333,
        "hallucination_rate": 0.06666666666666667,
        "weak_support_rate": 0.6,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.6047619047619048,
        "evidence_grounding_score": 0.3284722222222222
      },
      "factual_explanation": {
        "n": 1,
        "judge_score_mean": 0.9333333333333333,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.3333333333333333,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.8333333333333334,
        "evidence_grounding_score": 0.4458333333333333
      },
      "technical_comparison": {
        "n": 3,
        "judge_score_mean": 0.9333333333333335,
        "hallucination_rate": 0.2222222222222222,
        "weak_support_rate": 0.5555555555555555,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.6190476190476191,
        "evidence_grounding_score": 0.3431547619047619
      },
      "solution_design": {
        "n": 1,
        "judge_score_mean": 0.8666666666666668,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.6666666666666666,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.5714285714285714,
        "evidence_grounding_score": 0.25178571428571433
      }
    },
    "per_domain": {
      "citation_verification": {
        "n": 3,
        "judge_score_mean": 0.9555555555555556,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.2222222222222222,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.888888888888889,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "context_compression": {
        "n": 1,
        "judge_score_mean": 0.8666666666666668,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.6666666666666666,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.5,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "redblue_repair": {
        "n": 1,
        "judge_score_mean": 0.9333333333333333,
        "hallucination_rate": 0.3333333333333333,
        "weak_support_rate": 0.6666666666666666,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.5714285714285714,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "engineering_tradeoff": {
        "n": 3,
        "judge_score_mean": 0.888888888888889,
        "hallucination_rate": 0.1111111111111111,
        "weak_support_rate": 0.6666666666666666,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.5634920634920635,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      },
      "memory_retrieval": {
        "n": 2,
        "judge_score_mean": 0.8666666666666668,
        "hallucination_rate": 0.16666666666666666,
        "weak_support_rate": 0.8333333333333333,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.42857142857142855,
        "repair_precision": 0.0,
        "repair_coverage": 0.0
      }
    },
    "judge_score_dimensions": {
      "factuality": 0.5333333333333334,
      "coverage": 1.0,
      "citation_quality": 1.0,
      "structure": 1.0,
      "usefulness": 1.0
    },
    "multi_hop_subset": {
      "n": 7,
      "judge_score_mean": 0.8952380952380954,
      "hallucination_rate": 0.09523809523809523,
      "weak_support_rate": 0.619047619047619,
      "citation_coverage": 1.0,
      "atomic_support_rate": 0.5782312925170068,
      "repair_precision": 0.0,
      "repair_coverage": 0.0
    },
    "hotpot_style_subset": {
      "n": 0,
      "judge_score_mean": 0.0,
      "hallucination_rate": 0.0,
      "weak_support_rate": 0.0,
      "citation_coverage": 0.0,
      "atomic_support_rate": 0.0,
      "repair_precision": 0.0,
      "repair_coverage": 0.0
    },
    "repair_action_distribution": {}
  },
  "redblue": {
    "n": 10,
    "judge_score_mean": 0.9200000000000002,
    "judge_score_bootstrap_95_ci": [
      0.8933333333333334,
      0.9500000000000001
    ],
    "cohens_d": 3.3115253986947573,
    "factual_accuracy": 1.0,
    "hallucination_rate": 0.0,
    "weak_support_rate": 0.4,
    "citation_coverage": 1.0,
    "evidence_reuse_rate": 0.2966126194067371,
    "compression_ratio": 0.43842035416620256,
    "repair_success_rate": 1.0,
    "atomic_support_rate": 0.7642857142857142,
    "contradiction_detection_rate": 0.0,
    "repair_precision": 0.8833333333333334,
    "repair_coverage": 1.0,
    "repair_convergence_rate": 1.0,
    "repair_oscillation_rate": 0.5,
    "avg_repair_rounds": 2.0,
    "evidence_grounding_score": 0.3813492063492063,
    "avg_task_latency": 0.0188044311415251,
    "per_category": {
      "risk_analysis": {
        "n": 5,
        "judge_score_mean": 0.9,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.5,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.6976190476190477,
        "evidence_grounding_score": 0.35251984126984126
      },
      "factual_explanation": {
        "n": 1,
        "judge_score_mean": 0.9333333333333333,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.3333333333333333,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.8333333333333334,
        "evidence_grounding_score": 0.4458333333333333
      },
      "technical_comparison": {
        "n": 3,
        "judge_score_mean": 0.9666666666666667,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.16666666666666666,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.9166666666666666,
        "evidence_grounding_score": 0.4364087301587302
      },
      "solution_design": {
        "n": 1,
        "judge_score_mean": 0.8666666666666668,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.6666666666666666,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.5714285714285714,
        "evidence_grounding_score": 0.29583333333333334
      }
    },
    "per_domain": {
      "citation_verification": {
        "n": 3,
        "judge_score_mean": 0.9555555555555556,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.2222222222222222,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.888888888888889,
        "repair_precision": 1.0,
        "repair_coverage": 1.0
      },
      "context_compression": {
        "n": 1,
        "judge_score_mean": 0.8666666666666668,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.6666666666666666,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.5,
        "repair_precision": 1.0,
        "repair_coverage": 1.0
      },
      "redblue_repair": {
        "n": 1,
        "judge_score_mean": 1.0,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.0,
        "citation_coverage": 1.0,
        "atomic_support_rate": 1.0,
        "repair_precision": 0.5,
        "repair_coverage": 1.0
      },
      "engineering_tradeoff": {
        "n": 3,
        "judge_score_mean": 0.9,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.49999999999999994,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.7182539682539683,
        "repair_precision": 0.8888888888888888,
        "repair_coverage": 1.0
      },
      "memory_retrieval": {
        "n": 2,
        "judge_score_mean": 0.8833333333333334,
        "hallucination_rate": 0.0,
        "weak_support_rate": 0.5833333333333333,
        "citation_coverage": 1.0,
        "atomic_support_rate": 0.6607142857142857,
        "repair_precision": 0.8333333333333333,
        "repair_coverage": 1.0
      }
    },
    "judge_score_dimensions": {
      "factuality": 0.6000000000000001,
      "coverage": 1.0,
      "citation_quality": 1.0,
      "structure": 1.0,
      "usefulness": 1.0
    },
    "multi_hop_subset": {
      "n": 7,
      "judge_score_mean": 0.9047619047619049,
      "hallucination_rate": 0.0,
      "weak_support_rate": 0.47619047619047616,
      "citation_coverage": 1.0,
      "atomic_support_rate": 0.7108843537414966,
      "repair_precision": 0.9047619047619048,
      "repair_coverage": 1.0
    },
    "hotpot_style_subset": {
      "n": 0,
      "judge_score_mean": 0.0,
      "hallucination_rate": 0.0,
      "weak_support_rate": 0.0,
      "citation_coverage": 0.0,
      "atomic_support_rate": 0.0,
      "repair_precision": 0.0,
      "repair_coverage": 0.0
    },
    "repair_action_distribution": {
      "modify": 11,
      "delete": 3,
      "add": 5
    }
  }
}


## STDERR


Exit code: 0