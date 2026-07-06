# Evaluation Metrics Trace

Case: `baseline_vs_redblue`

## Summary

Baseline judge mean: `0.550`
Improved judge mean: `0.813`
Judge delta: `0.263`
Improved 95% CI: `[0.78, 0.86]`
Cohen's d vs baseline: `8.888`
Weak support delta: `-0.517`
Atomic support delta: `0.483`
Evidence grounding delta: `0.323`

## Interpretation

Improved config is better when judge_score_mean and atomic_support_rate increase, while weak_support_rate decreases. Cohen's d reports effect size relative to baseline.

## Learning Notes

- Baseline has weak support and low atomic grounding because verifier and red-blue repair are disabled.
- Baseline can still produce cited text, but weak claims remain unrepaired.
- Risk analysis suffers when unsupported claims are not repaired.
- Red-Blue improves the same case by repairing weak claims and preserving citations.
- Technical comparison improves when weak overclaims are modified rather than left untouched.
- Risk analysis improves when unsupported or contradicted claims are removed.