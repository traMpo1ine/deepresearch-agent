# Structured Output Parser Summary

Cases: `30`
Parse success: `30`
Parse success rate: `1.000`
By level: `{'1': 4, '2': 7, '3': 19}`

## Three Fallback Levels

- Level 1: strict `json.loads`.
- Level 2: fenced JSON or substring JSON extraction.
- Level 3: common JSON repair plus schema defaults.

This is an offline parser stress suite. The `1.000` success rate applies only to the 30 fixed corrupted-output cases in `data/examples/structured_output_cases.jsonl`.
