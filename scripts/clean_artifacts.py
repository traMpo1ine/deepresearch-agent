from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".venv", ".uv-cache", ".git"}
CACHE_DIRS = {".pytest_cache", ".ruff_cache"}


def is_inside_root(path: Path) -> bool:
    try:
        path.resolve().relative_to(ROOT.resolve())
        return True
    except ValueError:
        return False


def collect_targets(
    include_memory: bool,
    include_plans: bool,
    include_reports: bool,
    keep_examples: bool,
) -> list[Path]:
    targets: list[Path] = []
    targets.extend(path for path in ROOT.rglob("__pycache__") if not is_skipped(path))
    targets.extend(ROOT.glob("src/*.egg-info"))
    targets.extend(ROOT / name for name in CACHE_DIRS if (ROOT / name).exists())
    if include_memory:
        targets.extend(path for path in (ROOT / "data" / "memory").glob("*") if path.is_file())
    if include_plans:
        targets.extend(path for path in (ROOT / "reports" / "plans").rglob("*") if path.is_file())
    if include_reports:
        report_root = ROOT / "reports"
        for path in report_root.rglob("*"):
            if not path.is_file():
                continue
            if keep_examples and (report_root / "examples") in path.parents:
                continue
            if path.name == ".gitkeep":
                continue
            targets.append(path)
    return sorted(set(targets))


def is_skipped(path: Path) -> bool:
    try:
        relative = path.resolve().relative_to(ROOT.resolve())
    except ValueError:
        return True
    return any(part in SKIP_DIRS for part in relative.parts)


def remove_path(path: Path) -> None:
    if not is_inside_root(path):
        raise RuntimeError(f"Refusing to remove path outside workspace: {path}")
    if path.is_dir():
        for child in sorted(path.rglob("*"), reverse=True):
            if child.is_file():
                child.unlink()
            elif child.is_dir():
                child.rmdir()
        path.rmdir()
    elif path.exists():
        path.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean generated DeepResearch Agent artifacts.")
    parser.add_argument("--include-memory", action="store_true", help="Delete files under data/memory.")
    parser.add_argument("--include-plans", action="store_true", help="Delete generated plan JSON/Mermaid files.")
    parser.add_argument("--include-reports", action="store_true", help="Delete generated files under reports.")
    parser.add_argument("--keep-examples", action="store_true", help="Preserve reports/examples.")
    parser.add_argument("--dry-run", action="store_true", help="Print targets without deleting them.")
    args = parser.parse_args()

    targets = collect_targets(
        include_memory=args.include_memory,
        include_plans=args.include_plans,
        include_reports=args.include_reports,
        keep_examples=args.keep_examples,
    )
    for target in targets:
        print(target.relative_to(ROOT))
    if args.dry_run:
        return
    for target in targets:
        remove_path(target)


if __name__ == "__main__":
    main()
