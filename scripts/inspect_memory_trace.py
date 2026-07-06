from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from deepresearch_agent.memory_cases import (  # noqa: E402
    get_memory_case,
    inspect_memory_case,
    list_memory_cases_markdown,
    load_memory_cases,
    memory_payload_to_markdown,
    payload_json,
)


def run(case_id: str | None, list_only: bool, as_json: bool) -> None:
    if list_only:
        cases = load_memory_cases()
        if as_json:
            print(
                payload_json(
                    {
                        "cases": [
                            {
                                "id": case.id,
                                "expected_top_id": case.expected_top_id,
                                "learning_note": case.learning_note,
                            }
                            for case in cases
                        ]
                    }
                )
            )
        else:
            print(list_memory_cases_markdown(cases))
        return

    payload = inspect_memory_case(get_memory_case(case_id or "sqlite_vector_recall"))
    print(payload_json(payload) if as_json else memory_payload_to_markdown(payload))


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect SQLite memory and numpy vector recall.")
    parser.add_argument("--case", help="Memory case id. Defaults to sqlite_vector_recall.")
    parser.add_argument("--list", action="store_true", help="List available memory cases.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")
    args = parser.parse_args()
    run(args.case, args.list, args.json)


if __name__ == "__main__":
    main()
