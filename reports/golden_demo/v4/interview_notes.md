# Showcase Interview Notes

Question: 请基于下面三份公开资料，为一个可审计的 DeepResearch Agent 设计工程方案：说明为什么要分别评测检索与生成、如何保留引用溯源，以及如何把提示注入作为不可信输入处理。请区分资料明确支持的结论与工程推断，并给出可以落地的最小检查清单。
https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence
https://genai.owasp.org/llm-top-10/
https://arxiv.org/abs/2405.07437

## 60-Second Story

This run demonstrates the full DeepResearch pipeline: Planner builds a DAG, Coordinator executes search/read tasks with memory and compression, Writer emits cited claims, Verifier checks atomic claim grounding, and Red-Blue records repair actions.

## Numbers To Mention

- run id: `run_3318f752dcc5`
- tasks: `9`
- evidence: `29`
- recalled evidence: `0`
- live sources: `3`
- live-source lineage complete rate: `1.0`
- live-source cache hit rate: `0.0`
- provider operational rate: `1.0`
- provider retries: `0`
- circuit-open events: `0`
- compression ratio: `0.796`
- repair actions: `0`
- planner mode: `heuristic`
- llm backend: `mock`
- writer mode: `extractive`
- embedding provider: `openai_compatible`
- embedding model: `text-embedding-v4`
- embedding remote inputs: `48`
- embedding cache hits: `87`

## Tradeoff

The showcase remains offline by default. This keeps the demo reproducible and lets the engineering mechanisms be inspected without API cost or model nondeterminism.