from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from deepresearch_agent.redblue_cases import (  # noqa: E402
    get_redblue_case,
    inspect_redblue_case,
    list_redblue_cases_markdown,
    load_redblue_cases,
    payload_json,
    redblue_payload_to_markdown,
)


async def run(case_id: str | None, list_only: bool, as_json: bool) -> None:
    if list_only:
        cases = load_redblue_cases()
        if as_json:
            print(
                payload_json(
                    {
                        "cases": [
                            {
                                "id": case.id,
                                "expected_action": case.expected_action,
                                "learning_note": case.learning_note,
                            }
                            for case in cases
                        ]
                    }
                )
            )
        else:
            print(list_redblue_cases_markdown(cases))
        return

    case = get_redblue_case(case_id or "overclaim")
    _repaired, payload = await inspect_redblue_case(case)
    print(payload_json(payload) if as_json else redblue_payload_to_markdown(payload))


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect Red-Blue finding and repair traces.")
    parser.add_argument("--case", help="Red-Blue case id. Defaults to overclaim.")
    parser.add_argument("--list", action="store_true", help="List available Red-Blue cases.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")
    args = parser.parse_args()
    asyncio.run(run(args.case, args.list, args.json))


if __name__ == "__main__":
    main()
