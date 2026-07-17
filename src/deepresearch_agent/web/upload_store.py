from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from deepresearch_agent.corpus_profiles import CorpusProfile, build_profile
from deepresearch_agent.tools.web_fetch import detect_prompt_injection


ALLOWED_UPLOAD_SUFFIXES = {".pdf", ".md", ".txt", ".html"}
UPLOAD_ID_PATTERN = re.compile(r"^upload_(?:[0-9a-f]{16}|[0-9a-f]{64})$")


class AsyncReadable(Protocol):
    async def read(self, size: int = -1) -> bytes: ...


class UploadValidationError(ValueError):
    """Uploaded bytes do not match the accepted corpus formats."""


class UploadTooLargeError(UploadValidationError):
    """Uploaded body exceeded the configured byte limit."""


@dataclass(frozen=True, slots=True)
class UploadedCorpus:
    corpus_id: str
    original_name: str
    stored_name: str
    source_format: str
    content_sha256: str
    size_bytes: int
    chunk_count: int
    page_count: int | None
    title: str
    source_path: str
    corpus_path: str
    created_at: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class UploadedCorpusStore:
    """Content-addressed, bounded upload ingestion for local corpus profiles."""

    def __init__(self, root: str | Path, max_bytes: int = 10 * 1024 * 1024) -> None:
        self.root = Path(root).resolve()
        self.max_bytes = max(1024, max_bytes)
        self.incoming_dir = self.root / ".incoming"
        self.incoming_dir.mkdir(parents=True, exist_ok=True)

    async def ingest(
        self,
        original_name: str | None,
        stream: AsyncReadable,
    ) -> tuple[UploadedCorpus, bool]:
        safe_name = _safe_original_name(original_name)
        suffix = Path(safe_name).suffix.lower()
        if suffix not in ALLOWED_UPLOAD_SUFFIXES:
            raise UploadValidationError(
                "Only PDF, Markdown, TXT and HTML files are accepted."
            )
        incoming = self.incoming_dir / f"{uuid4().hex}.tmp"
        digest = hashlib.sha256()
        size = 0
        prefix = b""
        try:
            with incoming.open("wb") as handle:
                while True:
                    chunk = await stream.read(64 * 1024)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > self.max_bytes:
                        raise UploadTooLargeError(
                            f"Upload exceeds {self.max_bytes} bytes."
                        )
                    if len(prefix) < 8:
                        prefix += chunk[: 8 - len(prefix)]
                    digest.update(chunk)
                    handle.write(chunk)
            if size == 0:
                raise UploadValidationError("Uploaded file is empty.")
            self._validate_content(incoming, suffix, prefix)
            content_sha256 = digest.hexdigest()
            corpus_id = f"upload_{content_sha256[:16]}"
            existing = self.get(corpus_id)
            if existing is not None:
                if existing.content_sha256 == content_sha256:
                    return existing, False
                # Preserve existing short ids while making a detected prefix collision safe.
                corpus_id = f"upload_{content_sha256}"
                existing = self.get(corpus_id)
                if existing is not None:
                    return existing, False

            corpus_dir = self.root / corpus_id
            corpus_dir.mkdir(parents=True, exist_ok=True)
            stored_name = f"document{suffix}"
            source_path = corpus_dir / stored_name
            incoming.replace(source_path)
            corpus_path = corpus_dir / "corpus.jsonl"
            temporary_corpus = corpus_dir / f"corpus.{uuid4().hex}.tmp"
            build_profile(
                CorpusProfile(
                    key=corpus_id,
                    name=safe_name,
                    description="User-uploaded local corpus.",
                    source_dir=source_path,
                    output_path=temporary_corpus,
                )
            )
            rows = self._annotate_corpus(
                temporary_corpus,
                corpus_id=corpus_id,
                original_name=safe_name,
                uploaded_sha256=content_sha256,
            )
            if not rows:
                temporary_corpus.unlink(missing_ok=True)
                raise UploadValidationError("No readable text could be extracted from the upload.")
            temporary_corpus.replace(corpus_path)
            page_counts = [
                int(row.get("metadata", {}).get("source_page_count"))
                for row in rows
                if row.get("metadata", {}).get("source_page_count") is not None
            ]
            item = UploadedCorpus(
                corpus_id=corpus_id,
                original_name=safe_name,
                stored_name=stored_name,
                source_format=suffix.lstrip("."),
                content_sha256=content_sha256,
                size_bytes=size,
                chunk_count=len(rows),
                page_count=max(page_counts, default=None),
                title=str(rows[0].get("title") or safe_name),
                source_path=str(source_path),
                corpus_path=str(corpus_path),
                created_at=datetime.now(UTC).isoformat(),
            )
            self._write_manifest(corpus_dir / "manifest.json", item)
            return item, True
        finally:
            incoming.unlink(missing_ok=True)

    def get(self, corpus_id: str) -> UploadedCorpus | None:
        if not UPLOAD_ID_PATTERN.fullmatch(corpus_id):
            return None
        manifest = self.root / corpus_id / "manifest.json"
        if not manifest.is_file():
            return None
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        item = UploadedCorpus(**payload)
        if not Path(item.corpus_path).is_file() or not Path(item.source_path).is_file():
            return None
        return item

    def list(self, limit: int = 50) -> list[UploadedCorpus]:
        items = []
        for manifest in self.root.glob("upload_*/manifest.json"):
            item = self.get(manifest.parent.name)
            if item is not None:
                items.append(item)
        items.sort(key=lambda item: item.created_at, reverse=True)
        return items[: min(max(1, limit), 100)]

    def resolve_corpus_path(self, corpus_id: str) -> Path | None:
        item = self.get(corpus_id)
        return Path(item.corpus_path) if item is not None else None

    def is_ready(self) -> bool:
        return self.root.is_dir() and self.incoming_dir.is_dir()

    @staticmethod
    def _validate_content(path: Path, suffix: str, prefix: bytes) -> None:
        if suffix == ".pdf":
            if not prefix.startswith(b"%PDF-"):
                raise UploadValidationError("The .pdf file does not have a PDF signature.")
            return
        raw = path.read_bytes()
        if b"\x00" in raw:
            raise UploadValidationError("Text uploads may not contain NUL bytes.")
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise UploadValidationError("Text uploads must be UTF-8 encoded.") from exc

    @staticmethod
    def _annotate_corpus(
        path: Path,
        *,
        corpus_id: str,
        original_name: str,
        uploaded_sha256: str,
    ) -> list[dict[str, object]]:
        rows = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        for row in rows:
            metadata = row.setdefault("metadata", {})
            metadata.update(
                {
                    "upload_id": corpus_id,
                    "original_name": original_name,
                    "uploaded_content_sha256": uploaded_sha256,
                    "risk_flags": detect_prompt_injection(str(row.get("text") or "")),
                }
            )
            origin = str(metadata.get("content_origin") or "local_file")
            metadata["content_origin"] = f"uploaded_{origin}"
        path.write_text(
            "\n".join(json.dumps(row, ensure_ascii=False) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        return rows

    @staticmethod
    def _write_manifest(path: Path, item: UploadedCorpus) -> None:
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(item.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(path)


def _safe_original_name(name: str | None) -> str:
    candidate = (name or "upload.txt").replace("\\", "/").rsplit("/", maxsplit=1)[-1]
    candidate = "".join(character for character in candidate if character.isprintable()).strip()
    if not candidate or candidate in {".", ".."}:
        raise UploadValidationError("The upload filename is invalid.")
    return candidate[:200]
