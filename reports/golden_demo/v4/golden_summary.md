# Golden DeepResearch Demo

- Generated (UTC): `2026-07-17T08:35:02.223409+00:00`
- Run id: `run_3318f752dcc5`
- Overall status: **PASS**
- Generation backend: `mock`
- Embedding model: `text-embedding-v4`
- Public source hosts: `arxiv.org, genai.owasp.org, www.nist.gov`

## Acceptance checks

| Check | Passed | Observed |
|---|---|---|
| real_embedding_configured | True | openai_compatible |
| embedding_model_expected | True | text-embedding-v4 |
| public_sources_retrieved | True | 3 |
| source_lineage_complete | True | 1.0 |
| evidence_created | True | 29 |
| claims_created | True | 3 |
| public_source_cited | True | 3 |
| verification_trace_created | True | 3 |

## Boundary

This pack proves a controlled real-source and real-embedding execution. When `generation_backend=mock`, the Writer/Verifier/Red-Blue path is deterministic and must not be described as real-LLM generation. Run again with `--llm-backend deepseek` only after configuring `DEEPSEEK_API_KEY`.

## Reproduce

```powershell
uv run python scripts/run_golden_demo.py
```
