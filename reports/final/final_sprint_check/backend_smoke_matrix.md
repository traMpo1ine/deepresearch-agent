# LLM Backend Smoke Matrix

Run real backends: `False`
Attempted: `1`
Successful: `1`

| backend | model | env | attempted | success | latency | cost | error |
|---|---|---|---|---|---:|---:|---|
| mock | mock-researcher-v0 | True | True | True | 0.000 | 0.0000 |  |
| openai | gpt-4o-mini | False | False | False | 0.000 | 0.0000 |  |
| deepseek | deepseek-chat | False | False | False | 0.000 | 0.0000 |  |
| vllm | local-model | False | False | False | 0.000 | 0.0000 |  |

Real backend smoke results are configuration checks and should not be mixed with offline/mock ResearchBench metrics.