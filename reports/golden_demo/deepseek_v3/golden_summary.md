# Golden DeepResearch Demo

- Generated (UTC): `2026-07-17T09:15:21.027801+00:00`
- Run id: `run_1e7bd1426a19`
- Overall status: **PASS**
- Generation backend: `deepseek`
- Embedding model: `text-embedding-v4`
- Public source hosts: `arxiv.org, genai.owasp.org, www.nist.gov`
- Writer mode: `llm`
- Writer fallback: `False`
- LLM tokens: `1399`
- Estimated LLM cost (USD): `0.00023186`

## Acceptance checks

| Check | Passed | Observed |
|---|---|---|
| real_embedding_configured | True | openai_compatible |
| embedding_model_expected | True | text-embedding-v4 |
| public_sources_retrieved | True | 3 |
| source_lineage_complete | True | 1.0 |
| evidence_created | True | 54 |
| claims_created | True | 4 |
| public_source_cited | True | 3 |
| verification_trace_created | True | 4 |
| writer_generation_valid | True | {'mode': 'llm', 'fallback': False} |

## Boundary

This pack proves a controlled real-source, real-embedding, and DeepSeek Writer execution. The Writer acceptance check fails if the model returns no valid cited claims and the system falls back to extractive generation.

## Reproduce

```powershell
uv run python scripts/run_golden_demo.py --llm-backend deepseek
```
