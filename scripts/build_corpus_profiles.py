from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from deepresearch_agent.corpus_profiles import (  # noqa: E402
    CorpusProfile,
    build_all_profiles,
    build_profile,
    get_corpus_profile,
    list_corpus_profiles,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build local knowledge-base corpus profiles.")
    parser.add_argument("--profile", help="Build only one profile key.")
    parser.add_argument("--source-path", help="Build a custom corpus from one file or directory.")
    parser.add_argument("--output", default="data/corpus/profiles/custom_docs.jsonl")
    parser.add_argument("--key", default="custom_docs")
    parser.add_argument("--list", action="store_true", help="List available profiles.")
    args = parser.parse_args()
    if args.list:
        for profile in list_corpus_profiles():
            print(f"{profile.key}\t{profile.source_dir}\t{profile.output_path}")
        return
    if args.source_path:
        profile = CorpusProfile(
            key=args.key,
            name="Custom Documents",
            description="User-selected local document corpus.",
            source_dir=Path(args.source_path),
            output_path=Path(args.output),
        )
        paths = [build_profile(profile)]
    else:
        paths = [build_profile(get_corpus_profile(args.profile))] if args.profile else build_all_profiles()
    for path in paths:
        print(f"Built: {path}")


if __name__ == "__main__":
    main()
