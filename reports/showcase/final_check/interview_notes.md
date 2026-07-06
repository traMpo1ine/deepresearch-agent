# Showcase Interview Notes

Question: 为什么 DeepResearch Agent 需要引用验证？

## 60-Second Story

This run demonstrates the full DeepResearch pipeline: Planner builds a DAG, Coordinator executes search/read tasks with memory and compression, Writer emits cited claims, Verifier checks atomic claim grounding, and Red-Blue records repair actions.

## Numbers To Mention

- run id: `run_0c981f9a098d`
- tasks: `9`
- evidence: `14`
- recalled evidence: `5`
- compression ratio: `0.446`
- repair actions: `2`
- planner mode: `heuristic`
- llm backend: `mock`

## Tradeoff

The showcase remains offline by default. This keeps the demo reproducible and lets the engineering mechanisms be inspected without API cost or model nondeterminism.