from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from deepresearch_agent.verification_cases import (  # noqa: E402
    get_verification_case,
    inspect_verification_case,
    list_cases_markdown,
    load_verification_cases,
    payload_json,
    verification_payload_to_markdown,
)


async def run(case_id: str | None, list_only: bool, as_json: bool) -> None:
    if list_only:
        cases = load_verification_cases()
        if as_json:
            payload = [
                {
                    "id": case.id,
                    "expected_status": case.expected_status.value,
                    "learning_note": case.learning_note,
                }
                for case in cases
            ]
            print(payload_json({"cases": payload}))
        else:
            print(list_cases_markdown(cases))
        return

    case = get_verification_case(case_id or "supported")
    _verified, payload = await inspect_verification_case(case)
    print(payload_json(payload) if as_json else verification_payload_to_markdown(payload))


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect Verifier atomic claim traces.")
    parser.add_argument("--case", help="Verification case id. Defaults to supported.")
    parser.add_argument("--list", action="store_true", help="List available verification cases.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")
    args = parser.parse_args()
    asyncio.run(run(args.case, args.list, args.json))


if __name__ == "__main__":
    main()
