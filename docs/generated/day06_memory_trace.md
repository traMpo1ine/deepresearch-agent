# Memory Trace

Case: `sqlite_vector_recall`

Question: How can an agent reuse citation evidence?
Recall query: `citation audit evidence`
Run id: `run_sqlite_vector_recall`
Task id: `task_sqlite_vector_recall`
SQLite records: `3`
Vector index items: `3`
Expected top id: `ev_memory_citation`
Observed top id: `ev_memory_citation`
Top match ok: `true`

## Learning Note

SQLite keeps the inspectable source records, while the numpy vector index retrieves candidate evidence ids for recall.

## Vector Hits

### Hit 1

Evidence id: `ev_memory_citation`
Similarity: `0.212`
Title: Citation Memory
Quote: SQLite memory stores evidence records with source chunks and quotes.

### Hit 2

Evidence id: `ev_memory_vector`
Similarity: `0.157`
Title: Vector Recall
Quote: A numpy vector index retrieves similar evidence ids.

### Hit 3

Evidence id: `ev_memory_noise`
Similarity: `0.109`
Title: Cooking Note
Quote: A recipe uses salt.

## Lexical Hits

- `ev_memory_citation` Citation Memory | quote=SQLite memory stores evidence records with source chunks and quotes.
- `ev_memory_vector` Vector Recall | quote=A numpy vector index retrieves similar evidence ids.
