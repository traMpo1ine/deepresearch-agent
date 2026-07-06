# Agent Reliability Playbook

DeepResearch Agent should decompose complex questions into planning, retrieval, reading,
writing, verification, and repair stages. Each stage should leave structured traces so that
failures can be inspected instead of hidden inside the final answer.

Citation tracking is required because generated claims need to point back to concrete source
chunks and quote spans. A verifier can then compare atomic claims against evidence and expose
unsupported, partial, or contradicted statements.

Red-Blue repair is useful when the report contains weak support, missing limitations, wrong
citations, or over-strong language. Red identifies the failure mode and Blue applies explicit
ADD, DELETE, MODIFY, or VERIFY actions.
