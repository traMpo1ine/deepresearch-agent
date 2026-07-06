from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from deepresearch_agent.compression_cases import (  # noqa: E402
    compression_payload_to_markdown,
    get_compression_case,
    inspect_compression_case,
    list_compression_cases_markdown,
    load_compression_cases,
    payload_json,
)


def run(case_id: str | None, list_only: bool, as_json: bool) -> None:
    if list_only:
        cases = load_compression_cases()
        if as_json:
            print(
                payload_json(
                    {
                        "cases": [
                            {
                                "id": case.id,
                                "expected_quote_count": case.expected_quote_count,
                                "learning_note": case.learning_note,
                            }
                            for case in cases
                        ]
                    }
                )
            )
        else:
            print(list_compression_cases_markdown(cases))
        return

    case = get_compression_case(case_id or "quote_preservation")
    _context, payload = inspect_compression_case(case)
    print(payload_json(payload) if as_json else compression_payload_to_markdown(payload))


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect TextRank compression and quote preservation.")
    parser.add_argument("--case", help="Compression case id. Defaults to quote_preservation.")
    parser.add_argument("--list", action="store_true", help="List available compression cases.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")
    args = parser.parse_args()
    run(args.case, args.list, args.json)


if __name__ == "__main__":
    main()
