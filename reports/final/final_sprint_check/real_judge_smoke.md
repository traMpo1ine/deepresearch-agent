# Real LLM-as-Judge Smoke

Backend: `mock`
Model: `mock-researcher-v0`
Run real: `False`
Attempted: `5`
Successful: `5`
Skipped reason: ``

| case | success | overall | latency | parse_level | error |
|---|---|---:|---:|---:|---|
| rb_001 | True | 0.940 | 0.000 | 1 |  |
| rb_002 | True | 0.940 | 0.000 | 1 |  |
| rb_003 | True | 0.847 | 0.000 | 1 |  |
| rb_004 | True | 0.940 | 0.000 | 1 |  |
| rb_005 | True | 0.940 | 0.000 | 1 |  |

Real judge smoke is separate from offline/mock ResearchBench metrics.

```json
{
  "backend_status": {
    "backend": "mock",
    "model": "mock-researcher-v0",
    "timeout_seconds": 60.0,
    "max_retries": 2,
    "env_var": null,
    "env_configured": true,
    "offline_safe": true,
    "base_url": "local://mock"
  },
  "dataset": "data/benchmarks/researchbench.jsonl",
  "limit": 5,
  "run_real": false,
  "attempted": 5,
  "successful": 5,
  "skipped_reason": null,
  "rows": [
    {
      "case_id": "rb_001",
      "success": true,
      "latency_seconds": 3.1099654734134674e-05,
      "scores": {
        "factuality": 1.0,
        "coverage": 1.0,
        "citation_quality": 1.0,
        "structure": 0.7,
        "usefulness": 1.0,
        "overall": 0.9400000000000001
      },
      "parse_metadata": {
        "parse_ok": true,
        "parse_level": 1,
        "parse_error": null
      },
      "token_usage": {},
      "error": null
    },
    {
      "case_id": "rb_002",
      "success": true,
      "latency_seconds": 1.5099998563528061e-05,
      "scores": {
        "factuality": 1.0,
        "coverage": 1.0,
        "citation_quality": 1.0,
        "structure": 0.7,
        "usefulness": 1.0,
        "overall": 0.9400000000000001
      },
      "parse_metadata": {
        "parse_ok": true,
        "parse_level": 1,
        "parse_error": null
      },
      "token_usage": {},
      "error": null
    },
    {
      "case_id": "rb_003",
      "success": true,
      "latency_seconds": 1.3799872249364853e-05,
      "scores": {
        "factuality": 1.0,
        "coverage": 0.6666666666666666,
        "citation_quality": 1.0,
        "structure": 0.7,
        "usefulness": 0.8666666666666667,
        "overall": 0.8466666666666665
      },
      "parse_metadata": {
        "parse_ok": true,
        "parse_level": 1,
        "parse_error": null
      },
      "token_usage": {},
      "error": null
    },
    {
      "case_id": "rb_004",
      "success": true,
      "latency_seconds": 1.3699755072593689e-05,
      "scores": {
        "factuality": 1.0,
        "coverage": 1.0,
        "citation_quality": 1.0,
        "structure": 0.7,
        "usefulness": 1.0,
        "overall": 0.9400000000000001
      },
      "parse_metadata": {
        "parse_ok": true,
        "parse_level": 1,
        "parse_error": null
      },
      "token_usage": {},
      "error": null
    },
    {
      "case_id": "rb_005",
      "success": true,
      "latency_seconds": 1.0299962013959885e-05,
      "scores": {
        "factuality": 1.0,
        "coverage": 1.0,
        "citation_quality": 1.0,
        "structure": 0.7,
        "usefulness": 1.0,
        "overall": 0.9400000000000001
      },
      "parse_metadata": {
        "parse_ok": true,
        "parse_level": 1,
        "parse_error": null
      },
      "token_usage": {},
      "error": null
    }
  ],
  "boundary": "Real judge smoke is separate from offline/mock ResearchBench metrics."
}
```