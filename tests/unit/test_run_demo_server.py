import os
import runpy
from pathlib import Path


RUN_DEMO_SERVER = Path(__file__).resolve().parents[2] / "scripts" / "run_demo_server.py"
_load_env_file = runpy.run_path(str(RUN_DEMO_SERVER))["_load_env_file"]


def test_load_env_file_reads_keys_without_overwriting_environment(
    tmp_path: Path,
    monkeypatch,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# local configuration\nDEEPSEEK_API_KEY='file-key'\nEMBEDDING_MODEL=text-embedding-v4\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("DEEPSEEK_API_KEY", "process-key")
    monkeypatch.delenv("EMBEDDING_MODEL", raising=False)

    _load_env_file(env_file)

    assert os.environ["DEEPSEEK_API_KEY"] == "process-key"
    assert os.environ["EMBEDDING_MODEL"] == "text-embedding-v4"


def test_load_env_file_allows_missing_file(tmp_path: Path) -> None:
    _load_env_file(tmp_path / "missing.env")
