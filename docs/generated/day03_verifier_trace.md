# Verification Trace

Case: `mixed_atomic`

Claim: Citation tracking binds claims to evidence and vector search guarantees perfect recall.

Expected status: `partial`
Actual status: `partial`
Citation presence: `true`

## Learning Note

One atomic claim is supported, while the second atomic claim has no supporting evidence, so the aggregate status is partial.

## Verification Reason

Matched 5/10 important terms; missing=['guarantees', 'perfect', 'recall', 'search', 'vector'].

## Atomic Results

### Atomic 1

Text: Citation tracking binds claims to evidence
Status: `supported`
Best evidence: `ev_mixed`
Best quote: Citation tracking binds claims to evidence.
Term overlap: `1.00`
Quote overlap: `1.00`
Missing terms: `[]`
Contradiction cues: `[]`

Decision reason: Best evidence=ev_mixed; term_overlap=1.00; quote_overlap=1.00; contradiction_cues=[].

### Atomic 2

Text: vector search guarantees perfect recall
Status: `unsupported`
Best evidence: `ev_mixed`
Best quote: Citation tracking binds claims to evidence.
Term overlap: `0.00`
Quote overlap: `0.00`
Missing terms: `['guarantees', 'perfect', 'recall', 'search', 'vector']`
Contradiction cues: `[]`

Decision reason: Best evidence=ev_mixed; term_overlap=0.00; quote_overlap=0.00; contradiction_cues=[].
