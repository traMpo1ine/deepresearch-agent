# DeepResearch Agent Offline Research Report

**Question:** Why does DeepResearch need atomic verification and Red-Blue repair?

## Summary

A credible DeepResearch Agent should be engineered as an inspectable pipeline: planning creates task structure, retrieval and memory provide evidence, compression keeps useful context, and verification plus repair reduce unsupported claims.

## Sections

### System Design

The offline pipeline decomposes the research question, retrieves local evidence, compresses context, writes cited claims, and verifies the claim-evidence relation.

### Reliability Mechanisms

Citation tracking, verifier traces, and Red-Blue repair actions make failure modes visible instead of hiding them inside a final answer.

### Compressed Evidence Snapshot

[ev_eda1a159716d] Generated research reports are more trustworthy when important claims are bound to inspectable citations.
[ev_28f1d60710e2] Runs, tasks, evidence, claims, reports, and agent events can be stored in relational tables.
[ev_d189d3bf1ca1] In a research agent, multi-hop tasks test whether the system can connect planner decomposition, retrieval, synthesis, and verification rather than answer from a single snippet.
[ev_8a20388bcfd0] A planner decomposes the user question into search, reading, synthesis, verification, and repair tasks.
[ev_44fb121c9d84] The repair log should keep before and after text so improvements are auditable.
[ev_9e392d1d920a] A strong technical blog explains the problem, design choices, implementation details, experiments, failures, and next steps.
[ev_83eb6d2212bc] Metrics such as citation coverage and hallucination rate should come from reproducible evaluation scripts.
[ev_440955502f7b] TextRank scores sentences by building a sentence similarity graph and running a PageRank-style iteration.
[ev_440955502f7b] Compression that drops the cited quote can make later verification unreliable.
[ev_9a0d4d4dd00a] For internship preparation, blog posts shou

## Key Claims

1. DeepResearch Agent should bind important claims to inspectable evidence and source chunks. [ev_eda1a159716d] (supported, confidence=0.75)
   - verification: Matched 4/7 important terms; missing=['agent', 'chunks', 'deepresearch'].
2. Evidence suggests that a DAG coordinator with asyncio and semaphores can run independent research tasks concurrently while preserving dependency order. [ev_8a20388bcfd0] (partial, confidence=0.60)
   - verification: Matched 5/12 important terms; missing=['asyncio', 'coordinator', 'dependency', 'order', 'preserving'].
3. A Red-Blue repair loop can improve reliability by detecting weak claims and applying ADD, DELETE, MODIFY, or VERIFY actions. [ev_44fb121c9d84] (supported, confidence=0.75)
   - verification: Matched 7/11 important terms; missing=['applying', 'claims', 'detecting', 'reliability'].

## Evidence

- [ev_44fb121c9d84] Red-Blue Adversarial Repair (local://trust/red-blue, chunk=red_blue_repair#chunk-1). Quote: The repair log should keep before and after text so improvements are auditable.
- [ev_eda1a159716d] Citation Tracking and Claim Binding (local://trust/citations, chunk=citation_tracking#chunk-1). Quote: Generated research reports are more trustworthy when important claims are bound to inspectable citations.
- [ev_9a0d4d4dd00a] Technical Blogging for Engineering Projects (local://career/blog, chunk=technical_blog#chunk-1). Quote: For internship preparation, blog posts should connect code decisions to measurable outcomes and interview explanations.
- [ev_51667053afbb] Structured Outputs for Agent Systems (local://agent/structured-output, chunk=structured_outputs#chunk-1). Quote: Plans, evidence, claims, findings, repair actions, and evaluation results should be represented as typed objects that can be serialized to JSON.
- [ev_8bc726f4f613] Hallucination Detection in Research Agents (local://trust/hallucination, chunk=hallucination_detection#chunk-1). Quote: Hallucination detection checks whether claims are supported by retrieved evidence.
- [ev_83eb6d2212bc] Resume Alignment for Agent Projects (local://career/resume, chunk=resume_alignment#chunk-1). Quote: Metrics such as citation coverage and hallucination rate should come from reproducible evaluation scripts.
- [ev_28f1d60710e2] SQLite Shared Memory for Agents (local://memory/sqlite, chunk=sqlite_memory#chunk-1). Quote: Runs, tasks, evidence, claims, reports, and agent events can be stored in relational tables.
- [ev_8a20388bcfd0] Agent Planning and Task Decomposition (local://agent/planning, chunk=agent_planning#chunk-1). Quote: A planner decomposes the user question into search, reading, synthesis, verification, and repair tasks.
- [ev_9e392d1d920a] Technical Blogging for Engineering Projects (local://career/blog, chunk=technical_blog#chunk-1). Quote: A strong technical blog explains the problem, design choices, implementation details, experiments, failures, and next steps.
- [ev_d189d3bf1ca1] HotpotQA Style Multi-Hop Reasoning (local://eval/hotpotqa, chunk=hotpotqa_multihop#chunk-1). Quote: In a research agent, multi-hop tasks test whether the system can connect planner decomposition, retrieval, synthesis, and verification rather than answer from a single snippet.
- [ev_440955502f7b] TextRank Context Compression (local://compression/textrank, chunk=textrank_context#chunk-1). Quote: TextRank scores sentences by building a sentence similarity graph and running a PageRank-style iteration.

## Limitations

- This offline v1 uses deterministic local retrieval and heuristic verification.
- Real LLM backends are adapter-ready but should be enabled only after the offline pipeline is stable.

## Repair Actions

- MODIFY claim_4a520477d756: Claim is only partially supported by cited evidence.