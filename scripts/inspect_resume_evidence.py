from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from deepresearch_agent.resume_evidence import (  # noqa: E402
    build_resume_evidence_payload,
    list_resume_evidence,
    payload_to_json,
    payload_to_markdown,
)


def run(evidence_id: str | None, list_only: bool, as_json: bool) -> None:
    if list_only:
        payload = {
            "ids": [
                {
                    "id": entry.evidence_id,
                    "resume_bullet": entry.resume_bullet,
                }
                for entry in list_resume_evidence()
            ]
        }
        if as_json:
            print(payload_to_json(payload))
        else:
            lines = ["# Resume Evidence Cases", ""]
            for item in payload["ids"]:
                lines.append(f"- `{item['id']}`: {item['resume_bullet']}")
            print("\n".join(lines))
        return

    payload = build_resume_evidence_payload(evidence_id=evidence_id, root=ROOT)
    print(payload_to_json(payload) if as_json else payload_to_markdown(payload))


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect resume bullets and their project evidence.")
    parser.add_argument("--bullet", help="Resume evidence id to inspect.")
    parser.add_argument("--list", action="store_true", help="List available evidence ids.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")
    args = parser.parse_args()
    run(args.bullet, args.list, args.json)


if __name__ == "__main__":
    main()
