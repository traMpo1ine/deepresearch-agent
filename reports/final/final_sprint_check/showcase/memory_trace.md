# Showcase Memory Trace

Run id: `run_e21f88ac370d`
Memory path: `reports\final\final_sprint_check\showcase\memory.sqlite3`
Vector path: `reports\final\final_sprint_check\showcase\vector_index.npz`
Evidence in report: `14`
Claims in report: `3`

## Cited Evidence

- `ev_10d60d9acc61` Citation Tracking and Claim Binding | source=citation_tracking | quote=A citation id should point to a concrete evidence object, which points to a source document, chunk, and quote span.
- `ev_d3249fb397d5` Hallucination Detection in Research Agents | source=hallucination_detection | quote=A simple first verifier can combine citation presence, lexical overlap, and contradiction heuristics before using an LLM verifier.

## Vector Recall

- `ev_a480733fb781` score=0.265 title=SQLite Shared Memory for Agents quote=Runs, tasks, evidence, claims, reports, and agent events can be stored in relational tables.
- `ev_88d32ed9d2e7` score=0.265 title=SQLite Shared Memory for Agents quote=Runs, tasks, evidence, claims, reports, and agent events can be stored in relational tables.
- `ev_eb3b74501b38` score=0.239 title=Vector Database Strengths and Limitations quote=Their limitations include weaker exact auditing, sensitivity to embedding quality, extra indexing cost, and the need to keep vector ids synchronized with source records.
- `ev_e7dfa35d5581` score=0.239 title=Vector Database Strengths and Limitations quote=Their limitations include weaker exact auditing, sensitivity to embedding quality, extra indexing cost, and the need to keep vector ids synchronized with source records.
- `ev_4417dc7f378c` score=0.236 title=SQLite and Vector Retrieval Tradeoffs quote=A practical DeepResearch Agent often combines both: SQLite stores canonical records and the vector index stores ids for similarity search.