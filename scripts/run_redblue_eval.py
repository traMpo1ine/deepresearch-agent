from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from deepresearch_agent.redblue_fixture_eval import (  # noqa: E402
    evaluate_redblue_fixtures,
    redblue_eval_markdown,
)


async def run(fixture_path: str, output: str | None, as_json: bool) -> None:
    payload = await evaluate_redblue_fixtures(fixture_path)
    text = json.dumps(payload, ensure_ascii=False, indent=2) if as_json else redblue_eval_markdown(payload)
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
    print(text)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate Red-Blue fixture repair success.")
    parser.add_argument("--fixtures", default="data/adversarial/redblue_fixtures.jsonl")
    parser.add_argument("--output")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")
    args = parser.parse_args()
    asyncio.run(run(args.fixtures, args.output, args.json))


if __name__ == "__main__":
    main()
