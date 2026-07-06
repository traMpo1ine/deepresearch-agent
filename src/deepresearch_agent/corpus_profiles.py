from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


PROFILE_ROOT = Path("data/corpus_profiles")
PROFILE_OUTPUT_DIR = Path("data/corpus")
DEFAULT_PROFILE_OUTPUT = PROFILE_OUTPUT_DIR / "profiles"


@dataclass(frozen=True, slots=True)
class CorpusProfile:
    key: str
    name: str
    description: str
    source_dir: Path
    output_path: Path

    def to_dict(self) -> dict[str, str]:
        return {
            "key": self.key,
            "name": self.name,
            "description": self.description,
            "source_dir": str(self.source_dir),
            "output_path": str(self.output_path),
        }


DEFAULT_PROFILES = {
    "offline_agent_docs": ("Offline Agent Docs", "默认 DeepResearch Agent 工程说明资料。"),
    "resume_agent_docs": ("Resume Agent Docs", "面向简历与面试讲解的 Agent 项目资料。"),
    "paper_reading_docs": ("Paper Reading Docs", "面向论文阅读/文献调研场景的知识库资料。"),
    "local_kb_docs": ("Local KB Docs", "本地 Markdown/PDF 企业知识库式资料入口。"),
}


def list_corpus_profiles(root: Path = PROFILE_ROOT) -> list[CorpusProfile]:
    profiles = []
    for key, (name, description) in DEFAULT_PROFILES.items():
        source_dir = root / key
        output_path = DEFAULT_PROFILE_OUTPUT / f"{key}.jsonl"
        profiles.append(
            CorpusProfile(
                key=key,
                name=name,
                description=description,
                source_dir=source_dir,
                output_path=output_path,
            )
        )
    return profiles


def get_corpus_profile(key: str) -> CorpusProfile:
    for profile in list_corpus_profiles():
        if profile.key == key:
            return profile
    valid = ", ".join(profile.key for profile in list_corpus_profiles())
    raise KeyError(f"Unknown corpus profile: {key}. Valid profiles: {valid}")


def ensure_profile_built(key: str) -> Path:
    profile = get_corpus_profile(key)
    if not profile.output_path.exists():
        build_profile(profile)
    return profile.output_path


def build_all_profiles() -> list[Path]:
    return [build_profile(profile) for profile in list_corpus_profiles()]


def build_profile(profile: CorpusProfile) -> Path:
    docs = list(_iter_source_files(profile.source_dir))
    profile.output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for doc_index, path in enumerate(docs, start=1):
        text = _normalize_text(_read_source_text(path))
        if not text:
            continue
        for chunk_index, chunk in enumerate(_chunk_text(text), start=1):
            rows.append(
                {
                    "id": f"{profile.key}_{doc_index:02d}_{chunk_index:02d}",
                    "title": _title_from_path(path),
                    "url": f"profile://{profile.key}/{path.name}#chunk-{chunk_index}",
                    "text": chunk,
                    "source_type": "corpus_profile",
                    "source_format": path.suffix.lower().lstrip("."),
                    "topics": _infer_topics(profile.key, path, chunk),
                    "trust_level": "high",
                    "profile": profile.key,
                }
            )
    profile.output_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + ("\n" if rows else ""),
        encoding="utf-8",
    )
    return profile.output_path


def _iter_source_files(source_dir: Path) -> Iterable[Path]:
    if not source_dir.exists():
        return []
    return sorted(
        path
        for path in source_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in {".md", ".txt", ".html", ".pdf"}
    )


def _read_source_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _read_pdf_text(path)
    return path.read_text(encoding="utf-8")


def _read_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(page for page in pages if page.strip())
        if text.strip():
            return text
    except Exception:  # noqa: BLE001 - bad local PDFs should not break corpus building.
        pass
    return _extract_pdf_literal_text(path.read_bytes())


def _extract_pdf_literal_text(data: bytes) -> str:
    raw = data.decode("latin-1", errors="ignore")
    literals = re.findall(r"\(([^()]*)\)", raw)
    cleaned = [item.replace(r"\(", "(").replace(r"\)", ")") for item in literals]
    return " ".join(cleaned)


def _normalize_text(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"^\s*#+\s*", "", text, flags=re.M)
    return re.sub(r"\s+", " ", text).strip()


def _chunk_text(text: str, max_chars: int = 520) -> list[str]:
    sentences = re.split(r"(?<=[.!?。！？])\s+", text)
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if len(current) + len(sentence) + 1 > max_chars and current:
            chunks.append(current.strip())
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        chunks.append(current.strip())
    return chunks or [text[:max_chars]]


def _title_from_path(path: Path) -> str:
    lines = _read_source_text(path).splitlines()
    first = lines[0].strip() if lines else ""
    if first.startswith("#"):
        return first.lstrip("#").strip()
    return path.stem.replace("_", " ").title()


def _infer_topics(profile: str, path: Path, text: str) -> list[str]:
    lowered = f"{profile} {path.stem} {text}".lower()
    candidates = [
        "agent",
        "rag",
        "retrieval",
        "memory",
        "citation",
        "verification",
        "redblue",
        "evaluation",
        "resume",
        "paper",
        "knowledge_base",
    ]
    return [topic for topic in candidates if topic in lowered]
