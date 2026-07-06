# DeepResearch Agent Risk Analysis Report

**Question:** 为什么 DeepResearch Agent 需要引用验证？

## Summary

This report treats the question as a reliability problem: it identifies failure modes, mitigation mechanisms, verification signals, and remaining limitations.

## Sections

### Failure Modes

The answer should identify how research agents can fail through missing evidence, weak citations, or hidden contradictions.

### Mitigation and Verification

The system should make reliability mechanisms observable through verifier traces, citation checks, and repair actions.

### Compressed Evidence Snapshot

[ev_2f0c39f70b19] SQLite keeps structured tables for runs, tasks, evidence, claims, reports, verification traces, and repair actions.
[ev_ee689cbfa994] SQLite and vector retrieval solve different parts of an agent memory problem.
[ev_ebe5862a15c0] Their limitations include weaker exact auditing, sensitivity to embedding quality, extra indexing cost, and the need to keep vector ids synchronized with source records.
[ev_7c5b3d3b9b3a] Runs, tasks, evidence, claims, reports, and agent events can be stored in relational tables.
[ev_a8843be46ccf] A practical DeepResearch Agent often combines both: SQLite stores canonical records and the vector index stores ids for similarity search.
[ev_59afbb3813de] SQLite is strong for durable records, relational queries, audit trails, and exact traceability from runs to tasks, evidence, claims, reports, and events.
[ev_d1e5373a7cab] Metrics such as citation coverage and hallucination rate should come from reproducible evaluation scripts.
[ev_68b5a03989e6] The coordinator can retrieve from the vector index, load full evidence from SQLite, and still preserve citation traceability.
[ev_18272e560282] Common failure modes include shallow planning, duplicat

## Key Claims

1. DeepResearch Agents can fail when claims are not grounded in inspectable evidence. [ev_d07db64e3d8a] (supported, confidence=0.75)
   - verification: Matched 3/6 important terms; missing=['deepresearch', 'grounded', 'inspectable'].
2. Citation tracking helps connect each important claim to a concrete source chunk and quote span. [ev_e14a6e750d5c] (supported, confidence=0.75)
   - verification: Matched 7/9 important terms; missing=['connect', 'helps'].
3. Evidence suggests that Verifier and Red-Blue repair loops make weak support visible and provide explicit ADD, DELETE, MODIFY, or VERIFY actions. [ev_d07db64e3d8a] (partial, confidence=0.60)
   - verification: Matched 3/14 important terms; missing=['actions', 'delete', 'explicit', 'loops', 'modify'].

## Evidence

- [ev_18272e560282] Failure Modes in Deep Research Agents (local://agent/failure-modes, chunk=failure_modes#chunk-1). Quote: Common failure modes include shallow planning, duplicate evidence, unsupported claims, stale memory, over-compression, and judge bias.
- [ev_e14a6e750d5c] Citation Tracking and Claim Binding (local://trust/citations, chunk=citation_tracking#chunk-1). Quote: A citation id should point to a concrete evidence object, which points to a source document, chunk, and quote span.
- [ev_7c5b3d3b9b3a] SQLite Shared Memory for Agents (local://memory/sqlite, chunk=sqlite_memory#chunk-1). Quote: Runs, tasks, evidence, claims, reports, and agent events can be stored in relational tables.
- [ev_ee689cbfa994] SQLite and Vector Retrieval Tradeoffs (local://comparison/sqlite-vector-tradeoffs, chunk=sqlite_vector_tradeoffs#chunk-1). Quote: SQLite and vector retrieval solve different parts of an agent memory problem.
- [ev_a8843be46ccf] SQLite and Vector Retrieval Tradeoffs (local://comparison/sqlite-vector-tradeoffs, chunk=sqlite_vector_tradeoffs#chunk-2). Quote: A practical DeepResearch Agent often combines both: SQLite stores canonical records and the vector index stores ids for similarity search.
- [ev_03fc6a5662a4] SQLite Shared Memory for Agents (local://memory/sqlite, chunk=sqlite_memory#chunk-1). Quote: This makes debugging and reproducible experiments easier because every claim can be traced back to evidence and source chunks.
- [ev_2f0c39f70b19] Hybrid Memory Design for Research Agents (local://comparison/hybrid-memory-design, chunk=hybrid_memory_design#chunk-1). Quote: SQLite keeps structured tables for runs, tasks, evidence, claims, reports, verification traces, and repair actions.
- [ev_68b5a03989e6] Hybrid Memory Design for Research Agents (local://comparison/hybrid-memory-design, chunk=hybrid_memory_design#chunk-2). Quote: The coordinator can retrieve from the vector index, load full evidence from SQLite, and still preserve citation traceability.
- [ev_59afbb3813de] SQLite and Vector Retrieval Tradeoffs (local://comparison/sqlite-vector-tradeoffs, chunk=sqlite_vector_tradeoffs#chunk-1). Quote: SQLite is strong for durable records, relational queries, audit trails, and exact traceability from runs to tasks, evidence, claims, reports, and events.
- [ev_d1e5373a7cab] Resume Alignment for Agent Projects (local://career/resume, chunk=resume_alignment#chunk-1). Quote: Metrics such as citation coverage and hallucination rate should come from reproducible evaluation scripts.
- [ev_ebe5862a15c0] Vector Database Strengths and Limitations (local://comparison/vector-database-limits, chunk=vector_database_limits#chunk-1). Quote: Their limitations include weaker exact auditing, sensitivity to embedding quality, extra indexing cost, and the need to keep vector ids synchronized with source records.
- [ev_d7a311294ba8] Vector Database Strengths and Limitations (local://comparison/vector-database-limits, chunk=vector_database_limits#chunk-2). Quote: For small offline projects, a numpy index can teach cosine similarity before introducing a production vector database.
- [ev_3eac11c84514] TextRank Context Compression (local://compression/textrank, chunk=textrank_context#chunk-1). Quote: In deep research, compression should keep high-salience sentences while preserving quoted evidence needed for citation checks.
- [ev_d07db64e3d8a] Hallucination Detection in Research Agents (local://trust/hallucination, chunk=hallucination_detection#chunk-1). Quote: A simple first verifier can combine citation presence, lexical overlap, and contradiction heuristics before using an LLM verifier.

## Limitations

- This offline v1 uses deterministic local retrieval and heuristic verification.
- Real LLM backends are adapter-ready but should be enabled only after the offline pipeline is stable.
- Some retrieved evidence was not fully synthesized; future runs should expand coverage.

## Repair Actions

- MODIFY claim_f234c8c6cc04: Claim is only partially supported by cited evidence.
- ADD report.limitations: Some high-ranked evidence is not reflected in the claims.