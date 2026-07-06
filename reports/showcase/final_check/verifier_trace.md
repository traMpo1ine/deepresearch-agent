# Showcase Verifier Trace

## Claim 1

DeepResearch Agents can fail when claims are not grounded in inspectable evidence.

Status: `supported`
Confidence: `0.75`
Citations: `['ev_d07db64e3d8a']`
Reason: Matched 3/6 important terms; missing=['deepresearch', 'grounded', 'inspectable'].

### Atomic 1

DeepResearch Agents can fail when claims are not grounded in inspectable evidence

Status: `supported`
Best evidence: `ev_d07db64e3d8a`
Term overlap: `0.50`
Quote overlap: `0.00`
Missing terms: `['deepresearch', 'grounded', 'inspectable']`
Decision: Best evidence=ev_d07db64e3d8a; term_overlap=0.50; quote_overlap=0.00; contradiction_cues=[].

## Claim 2

Citation tracking helps connect each important claim to a concrete source chunk and quote span.

Status: `supported`
Confidence: `0.75`
Citations: `['ev_e14a6e750d5c']`
Reason: Matched 7/9 important terms; missing=['connect', 'helps'].

### Atomic 1

Citation tracking helps connect each important claim to a concrete source chunk

Status: `supported`
Best evidence: `ev_e14a6e750d5c`
Term overlap: `0.75`
Quote overlap: `0.50`
Missing terms: `['connect', 'helps']`
Decision: Best evidence=ev_e14a6e750d5c; term_overlap=0.75; quote_overlap=0.50; contradiction_cues=[].

### Atomic 2

quote span

Status: `supported`
Best evidence: `ev_e14a6e750d5c`
Term overlap: `1.00`
Quote overlap: `1.00`
Missing terms: `[]`
Decision: Best evidence=ev_e14a6e750d5c; term_overlap=1.00; quote_overlap=1.00; contradiction_cues=[].

## Claim 3

Evidence suggests that Verifier and Red-Blue repair loops make weak support visible and provide explicit ADD, DELETE, MODIFY, or VERIFY actions.

Status: `partial`
Confidence: `0.60`
Citations: `['ev_d07db64e3d8a']`
Reason: Matched 3/14 important terms; missing=['actions', 'delete', 'explicit', 'loops', 'modify'].

### Atomic 1

Evidence suggests that Verifier

Status: `supported`
Best evidence: `ev_d07db64e3d8a`
Term overlap: `0.67`
Quote overlap: `0.33`
Missing terms: `['suggests']`
Decision: Best evidence=ev_d07db64e3d8a; term_overlap=0.67; quote_overlap=0.33; contradiction_cues=[].

### Atomic 2

Red-Blue repair loops make weak support visible

Status: `partial`
Best evidence: `ev_d07db64e3d8a`
Term overlap: `0.20`
Quote overlap: `0.00`
Missing terms: `['loops', 'red-blue', 'repair', 'visible']`
Decision: Best evidence=ev_d07db64e3d8a; term_overlap=0.20; quote_overlap=0.00; contradiction_cues=[].

### Atomic 3

provide explicit ADD, DELETE, MODIFY, or VERIFY actions

Status: `unsupported`
Best evidence: `ev_d07db64e3d8a`
Term overlap: `0.00`
Quote overlap: `0.00`
Missing terms: `['actions', 'delete', 'explicit', 'modify', 'provide', 'verify']`
Decision: Best evidence=ev_d07db64e3d8a; term_overlap=0.00; quote_overlap=0.00; contradiction_cues=[].
