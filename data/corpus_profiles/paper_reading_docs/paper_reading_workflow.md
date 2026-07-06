# Paper Reading Workflow

A paper-reading DeepResearch Agent should preserve source-grounded evidence while summarizing
methods, claims, limitations, and evaluation settings. The system should keep figure or table
references near the relevant prose when available.

For academic reading tasks, hallucination control depends on citation coverage and quote
preservation. Claims about a paper should cite the exact source chunk that supports them.

Evaluation can include factuality, coverage, citation quality, structure, usefulness, and
failure-case analysis. Bootstrap confidence intervals are useful when the benchmark size is
small and the mean score may be unstable.
