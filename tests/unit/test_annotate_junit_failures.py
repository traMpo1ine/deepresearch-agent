from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_script():
    script_path = Path("scripts/annotate_junit_failures.py")
    spec = importlib.util.spec_from_file_location("annotate_junit_failures", script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_annotate_junit_failures_emits_test_name_and_message(tmp_path, capsys) -> None:
    module = _load_script()
    report = tmp_path / "pytest.xml"
    report.write_text(
        """
        <testsuites>
          <testsuite>
            <testcase classname="tests.test_demo" name="test_failure" file="tests/test_demo.py" line="7">
              <failure message="expected: true">traceback details</failure>
            </testcase>
          </testsuite>
        </testsuites>
        """,
        encoding="utf-8",
    )

    count = module.annotate(report)
    output = capsys.readouterr().out

    assert count == 1
    assert "::error file=tests/test_demo.py,line=7" in output
    assert "tests.test_demo%3A%3Atest_failure" in output
    assert "expected%3A true" in output
