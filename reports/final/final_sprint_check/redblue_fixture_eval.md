# Red-Blue Fixture Evaluation

Cases: `80`
Repair success before: `0.425`
Repair success after: `1.000`
Repair success delta: `0.575`
Action accuracy: `1.000`
Repair precision: `1.000`
Repair coverage: `1.000`
Convergence rate: `1.000`
Oscillation rate: `0.000`
Action distribution: `{'delete': 36, 'modify': 25, 'verify': 10, 'add': 9}`

## Per Failure Mode

| failure_mode | n | before | after | action_accuracy | repair_coverage |
|---|---:|---:|---:|---:|---:|
| no_citation | 5 | 0.000 | 1.000 | 1.000 | 1.000 |
| contradiction | 6 | 0.000 | 1.000 | 1.000 | 1.000 |
| overclaim | 9 | 0.667 | 1.000 | 1.000 | 1.000 |
| partial_support | 1 | 1.000 | 1.000 | 1.000 | 1.000 |
| clean_supported | 10 | 1.000 | 1.000 | 1.000 | 1.000 |
| omission | 8 | 0.000 | 1.000 | 1.000 | 1.000 |
| wrong_citation | 5 | 0.000 | 1.000 | 1.000 | 1.000 |
| stale_memory | 5 | 0.800 | 1.000 | 1.000 | 1.000 |
| over_compression | 5 | 0.400 | 1.000 | 1.000 | 1.000 |
| vague_claim | 4 | 1.000 | 1.000 | 1.000 | 1.000 |
| metric_misuse | 5 | 0.000 | 1.000 | 1.000 | 1.000 |
| conflict_omission | 1 | 0.000 | 1.000 | 1.000 | 1.000 |
| oscillation_risk | 1 | 1.000 | 1.000 | 1.000 | 1.000 |
| fallback_policy | 3 | 0.333 | 1.000 | 1.000 | 1.000 |
| json_fallback_overclaim | 5 | 0.400 | 1.000 | 1.000 | 1.000 |
| traceability | 3 | 0.000 | 1.000 | 1.000 | 1.000 |
| backend_boundary | 2 | 1.000 | 1.000 | 1.000 | 1.000 |
| preflight_boundary | 2 | 0.500 | 1.000 | 1.000 | 1.000 |

## Per Source Of Error

| source_of_error | n | before | after | action_accuracy |
|---|---:|---:|---:|---:|
| no_citation | 3 | 0.000 | 1.000 | 1.000 |
| contradiction | 4 | 0.000 | 1.000 | 1.000 |
| overclaim | 6 | 0.833 | 1.000 | 1.000 |
| partial_support | 1 | 1.000 | 1.000 | 1.000 |
| clean_supported | 6 | 1.000 | 1.000 | 1.000 |
| omission | 4 | 0.000 | 1.000 | 1.000 |
| wrong_citation | 3 | 0.000 | 1.000 | 1.000 |
| stale_memory | 4 | 1.000 | 1.000 | 1.000 |
| over_compression | 2 | 1.000 | 1.000 | 1.000 |
| vague_claim | 1 | 1.000 | 1.000 | 1.000 |
| metric_misuse | 3 | 0.000 | 1.000 | 1.000 |
| conflict_omission | 1 | 0.000 | 1.000 | 1.000 |
| oscillation_risk | 1 | 1.000 | 1.000 | 1.000 |
| fallback_policy | 1 | 1.000 | 1.000 | 1.000 |
| json_fallback_overclaim | 1 | 1.000 | 1.000 | 1.000 |
| traceability | 1 | 0.000 | 1.000 | 1.000 |
| missing_citation | 2 | 0.000 | 1.000 | 1.000 |
| citation_mismatch | 2 | 0.000 | 1.000 | 1.000 |
| over_generalization | 1 | 0.000 | 1.000 | 1.000 |
| logic_conflict | 1 | 0.000 | 1.000 | 1.000 |
| missing_limitation | 2 | 0.000 | 1.000 | 1.000 |
| vague_language | 3 | 1.000 | 1.000 | 1.000 |
| quote_loss | 1 | 0.000 | 1.000 | 1.000 |
| parser_overclaim | 1 | 0.000 | 1.000 | 1.000 |
| false_positive_check | 1 | 1.000 | 1.000 | 1.000 |
| metric_overclaim | 1 | 0.000 | 1.000 | 1.000 |
| audit_contradiction | 1 | 0.000 | 1.000 | 1.000 |
| provider_boundary | 2 | 1.000 | 1.000 | 1.000 |
| fallback_overclaim | 1 | 0.000 | 1.000 | 1.000 |
| cautious_claim | 1 | 1.000 | 1.000 | 1.000 |
| domain_overgeneralization | 1 | 1.000 | 1.000 | 1.000 |
| parser_policy_conflict | 1 | 0.000 | 1.000 | 1.000 |
| supported_claim | 3 | 1.000 | 1.000 | 1.000 |
| external_validity_overclaim | 1 | 0.000 | 1.000 | 1.000 |
| repair_policy_conflict | 1 | 0.000 | 1.000 | 1.000 |
| missing_backend_boundary | 1 | 0.000 | 1.000 | 1.000 |
| limitation_loss | 1 | 0.000 | 1.000 | 1.000 |
| warning_omission | 1 | 1.000 | 1.000 | 1.000 |
| metric_confusion | 1 | 0.000 | 1.000 | 1.000 |
| audit_loss | 1 | 0.000 | 1.000 | 1.000 |
| transparency_conflict | 1 | 0.000 | 1.000 | 1.000 |
| preflight_overclaim | 1 | 0.000 | 1.000 | 1.000 |
| missing_eval_boundary | 1 | 0.000 | 1.000 | 1.000 |
| stale_memory_overclaim | 1 | 0.000 | 1.000 | 1.000 |
| hallucination_risk | 1 | 0.000 | 1.000 | 1.000 |
| testing_overclaim | 1 | 0.000 | 1.000 | 1.000 |