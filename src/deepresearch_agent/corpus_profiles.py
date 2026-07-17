from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
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


@dataclass(frozen=True, slots=True)
class SourceSection:
    text: str
    page_number: int | None = None
    page_count: int | None = None


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
        sections = _read_source_sections(path)
        normalized_sections = []
        for section in sections:
            normalized = _normalize_text(section.text)
            if normalized:
                normalized_sections.append((section, normalized))
        source_text = " ".join(text for _, text in normalized_sections)
        if not source_text:
            continue
        source_hash = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
        source_modified_at = datetime.fromtimestamp(
            path.stat().st_mtime, tz=timezone.utc
        ).isoformat()
        title = _title_from_text(path, "\n".join(section.text for section in sections))
        global_chunk_index = 0
        for section, text in normalized_sections:
            for page_chunk_index, chunk in enumerate(_chunk_text(text), start=1):
                global_chunk_index += 1
                page = section.page_number
                chunk_id = (
                    f"{profile.key}_{doc_index:02d}_p{page:03d}_{page_chunk_index:02d}"
                    if page is not None
                    else f"{profile.key}_{doc_index:02d}_{global_chunk_index:02d}"
                )
                anchor = (
                    f"page={page}&chunk={page_chunk_index}"
                    if page is not None
                    else f"chunk-{global_chunk_index}"
                )
                metadata: dict[str, object] = {
                    "content_origin": "local_pdf_page" if page is not None else "local_file",
                    "fetch_status": "local_read",
                    "content_sha256": source_hash,
                    "chunk_sha256": hashlib.sha256(chunk.encode("utf-8")).hexdigest(),
                    "retrieved_at": source_modified_at,
                    "source_name": path.name,
                    "source_size_bytes": path.stat().st_size,
                    "source_chunk_id": chunk_id,
                }
                if page is not None:
                    metadata.update(
                        {
                            "page_number": page,
                            "page_start": page,
                            "page_end": page,
                            "source_page_count": section.page_count,
                            "citation_locator": f"p. {page}",
                        }
                    )
                rows.append(
                    {
                        "id": chunk_id,
                        "title": title,
                        "url": f"profile://{profile.key}/{path.name}#{anchor}",
                        "text": chunk,
                        "source_type": "corpus_profile",
                        "source_format": path.suffix.lower().lstrip("."),
                        "topics": _infer_topics(profile.key, path, chunk),
                        "trust_level": "high",
                        "profile": profile.key,
                        "metadata": metadata,
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
    if source_dir.is_file():
        supported = {".md", ".txt", ".html", ".pdf"}
        return [source_dir] if source_dir.suffix.lower() in supported else []
    return sorted(
        path
        for path in source_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in {".md", ".txt", ".html", ".pdf"}
    )


def _read_source_text(path: Path) -> str:
    return "\n".join(section.text for section in _read_source_sections(path))


def _read_source_sections(path: Path) -> list[SourceSection]:
    if path.suffix.lower() == ".pdf":
        return _read_pdf_sections(path)
    return [SourceSection(path.read_text(encoding="utf-8"))]


def _read_pdf_sections(path: Path) -> list[SourceSection]:
    page_count: int | None = None
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        page_count = len(reader.pages)
        sections = [
            SourceSection(page.extract_text() or "", page_number=index, page_count=page_count)
            for index, page in enumerate(reader.pages, start=1)
        ]
        if any(section.text.strip() for section in sections):
            return [section for section in sections if section.text.strip()]
    except Exception:  # noqa: BLE001 - bad local PDFs should not break corpus building.
        pass
    fallback = _extract_pdf_literal_text(path.read_bytes())
    return [SourceSection(fallback, page_count=page_count)] if fallback else []


def _read_pdf_text(path: Path) -> str:
    return "\n".join(section.text for section in _read_pdf_sections(path))


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


def _title_from_text(path: Path, text: str) -> str:
    lines = text.splitlines()
    first = lines[0].strip() if lines else ""
    if first.startswith("#"):
        return first.lstrip("#").strip()
    if path.suffix.lower() == ".pdf":
        title_parts = []
        for raw_line in lines[:8]:
            line = raw_line.strip()
            if not line:
                continue
            if title_parts and re.match(
                r"^(?:\d+(?:st|nd|rd|th)\b|abstract\b|keywords?\b)",
                line,
                flags=re.IGNORECASE,
            ):
                break
            title_parts.append(line)
            if len(" ".join(title_parts)) >= 160:
                break
        title = " ".join(title_parts)
        if 8 <= len(title) <= 240:
            return title
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
