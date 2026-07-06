# DeepResearch Agent Offline v2 Example

This curated example demonstrates the intended report shape.

## What To Notice

- Claims include citation ids.
- Evidence objects point to source chunks and quotes.
- Verification traces explain support level.
- Red-Blue repair actions are auditable.

Generate a fresh example with:

```powershell
uv run python scripts/run_research.py "Why does DeepResearch need verification?" --output reports/examples/fresh.md --output-json reports/examples/fresh.json
```
