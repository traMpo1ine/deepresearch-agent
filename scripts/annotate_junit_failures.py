from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path


def _escape(value: str) -> str:
    return (
        value.replace("%", "%25")
        .replace("\r", "%0D")
        .replace("\n", "%0A")
        .replace(":", "%3A")
        .replace(",", "%2C")
    )


def annotate(path: Path) -> int:
    root = ET.parse(path).getroot()
    failures = 0
    for testcase in root.iter("testcase"):
        problem = testcase.find("failure")
        if problem is None:
            problem = testcase.find("error")
        if problem is None:
            continue
        failures += 1
        file_name = testcase.get("file") or "tests"
        line = testcase.get("line") or "1"
        test_name = "::".join(
            value
            for value in (testcase.get("classname"), testcase.get("name"))
            if value
        )
        message = problem.get("message") or (problem.text or "pytest failure")
        print(
            f"::error file={_escape(file_name)},line={line},"
            f"title={_escape(test_name)}::{_escape(message[:3000])}"
        )
    print(f"Annotated {failures} pytest failure(s) from {path.as_posix()}.")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit GitHub annotations from pytest JUnit XML.")
    parser.add_argument("junit_xml", type=Path)
    args = parser.parse_args()
    if not args.junit_xml.exists():
        raise SystemExit(f"JUnit file does not exist: {args.junit_xml}")
    annotate(args.junit_xml)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
