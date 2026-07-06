# Showcase Compression Trace

Question: 为什么 DeepResearch Agent 需要引用验证？
Original chars: `3865`
Compressed chars: `1724`
Compression ratio: `0.446`
Selected sentences: `14`

## Selected Sentences

### Sentence 1

SQLite keeps structured tables for runs, tasks, evidence, claims, reports, verification traces, and repair actions.

Evidence: `ev_2f0c39f70b19`
Source: `hybrid_memory_design`
Preserved quote: `true`
Score: `1.162`

### Sentence 2

SQLite and vector retrieval solve different parts of an agent memory problem.

Evidence: `ev_ee689cbfa994`
Source: `sqlite_vector_tradeoffs`
Preserved quote: `true`
Score: `1.074`

### Sentence 3

Their limitations include weaker exact auditing, sensitivity to embedding quality, extra indexing cost, and the need to keep vector ids synchronized with source records.

Evidence: `ev_ebe5862a15c0`
Source: `vector_database_limits`
Preserved quote: `true`
Score: `1.069`

### Sentence 4

Runs, tasks, evidence, claims, reports, and agent events can be stored in relational tables.

Evidence: `ev_7c5b3d3b9b3a`
Source: `sqlite_memory`
Preserved quote: `true`
Score: `1.067`

### Sentence 5

A practical DeepResearch Agent often combines both: SQLite stores canonical records and the vector index stores ids for similarity search.

Evidence: `ev_a8843be46ccf`
Source: `sqlite_vector_tradeoffs`
Preserved quote: `true`
Score: `1.056`

### Sentence 6

SQLite is strong for durable records, relational queries, audit trails, and exact traceability from runs to tasks, evidence, claims, reports, and events.

Evidence: `ev_59afbb3813de`
Source: `sqlite_vector_tradeoffs`
Preserved quote: `true`
Score: `1.002`

### Sentence 7

Metrics such as citation coverage and hallucination rate should come from reproducible evaluation scripts.

Evidence: `ev_d1e5373a7cab`
Source: `resume_alignment`
Preserved quote: `true`
Score: `0.925`

### Sentence 8

The coordinator can retrieve from the vector index, load full evidence from SQLite, and still preserve citation traceability.

Evidence: `ev_68b5a03989e6`
Source: `hybrid_memory_design`
Preserved quote: `true`
Score: `0.911`

### Sentence 9

Common failure modes include shallow planning, duplicate evidence, unsupported claims, stale memory, over-compression, and judge bias.

Evidence: `ev_18272e560282`
Source: `failure_modes`
Preserved quote: `true`
Score: `1.000`

### Sentence 10

A citation id should point to a concrete evidence object, which points to a source document, chunk, and quote span.

Evidence: `ev_e14a6e750d5c`
Source: `citation_tracking`
Preserved quote: `true`
Score: `1.000`

### Sentence 11

This makes debugging and reproducible experiments easier because every claim can be traced back to evidence and source chunks.

Evidence: `ev_03fc6a5662a4`
Source: `sqlite_memory`
Preserved quote: `true`
Score: `1.000`

### Sentence 12

For small offline projects, a numpy index can teach cosine similarity before introducing a production vector database.

Evidence: `ev_d7a311294ba8`
Source: `vector_database_limits`
Preserved quote: `true`
Score: `1.000`

### Sentence 13

In deep research, compression should keep high-salience sentences while preserving quoted evidence needed for citation checks.

Evidence: `ev_3eac11c84514`
Source: `textrank_context`
Preserved quote: `true`
Score: `1.000`

### Sentence 14

A simple first verifier can combine citation presence, lexical overlap, and contradiction heuristics before using an LLM verifier.

Evidence: `ev_d07db64e3d8a`
Source: `hallucination_detection`
Preserved quote: `true`
Score: `1.000`
