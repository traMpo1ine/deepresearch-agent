import importlib.util
from pathlib import Path


spec = importlib.util.spec_from_file_location(
    "clean_artifacts",
    Path("scripts/clean_artifacts.py"),
)
clean_artifacts = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(clean_artifacts)


def test_clean_artifacts_does_not_target_docs_or_benchmarks() -> None:
    targets = clean_artifacts.collect_targets(
        include_memory=True,
        include_plans=True,
        include_reports=True,
        keep_examples=True,
    )
    as_text = [str(path).replace("\\", "/") for path in targets]

    assert not any("/docs/" in path for path in as_text)
    assert not any("/data/benchmarks/" in path for path in as_text)
    assert not any("/reports/examples/" in path for path in as_text)
