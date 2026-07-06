from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from deepresearch_agent.structured_output_cases import (  # noqa: E402
    inspect_structured_output_case,
    load_structured_output_cases,
    structured_output_markdown,
    structured_output_summary,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect three-level structured JSON fallback.")
    parser.add_argument("--case", help="Structured output case id.")
    parser.add_argument("--list", action="store_true", help="List available cases.")
    parser.add_argument("--summary", action="store_true", help="Show parse success summary.")
    parser.add_argument("--output", help="Optional path to write the report.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")
    args = parser.parse_args()

    if args.list:
        payload = {
            "cases": [
                {
                    "id": case.id,
                    "expected_ok": case.expected_ok,
                    "expected_level": case.expected_level,
                }
                for case in load_structured_output_cases()
            ]
        }
    elif args.summary or not args.case:
        payload = {"summary": structured_output_summary()}
    else:
        payload = inspect_structured_output_case(args.case)
    text = (
        json.dumps(payload, ensure_ascii=False, indent=2)
        if args.json
        else structured_output_markdown(payload)
    )
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
