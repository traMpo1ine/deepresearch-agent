# Orchestration Stress Summary

Cases: `6`
Mean timeout recovery rate: `0.167`
Mean batch replan success rate: `0.167`
Mean fallback report rate: `0.333`

Cases:

- `task_timeout`
- `retry_success`
- `retry_exhausted`
- `batch_replan`
- `evidence_insufficient`
- `global_fallback`

## How To Read This

This trace is not an online reliability claim. It is a fixed offline stress suite used to explain how the coordinator handles failure paths:

- Level 1: task-local timeout and retry.
- Level 2: batch-level lightweight replan.
- Level 3: fallback report when evidence is insufficient.

The purpose is to make failure behavior inspectable, not to claim production-grade distributed scheduling.
