from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from deepresearch_agent.compression import TextRankCompressor
from deepresearch_agent.schemas import CompressedContext, Evidence
from deepresearch_agent.schemas.serialization import to_jsonable


DEFAULT_COMPRESSION_CASES_PATH = Path("data/examples/compression_cases.jsonl")


@dataclass(slots=True)
class CompressionCase:
    id: str
    question: str
    evidence: list[Evidence]
    max_sentences: int
    l1_top_k: int
    expected_quote_count: int
    learning_note: str


def load_compression_cases(path: str | Path = DEFAULT_COMPRESSION_CASES_PATH) -> list[CompressionCase]:
    cases: list[CompressionCase] = []
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        cases.append(_case_from_raw(json.loads(line), line_number))
    return cases


def get_compression_case(
    case_id: str,
    path: str | Path = DEFAULT_COMPRESSION_CASES_PATH,
) -> CompressionCase:
    cases = load_compression_cases(path)
    for case in cases:
        if case.id == case_id:
            return case
    available = ", ".join(case.id for case in cases)
    raise ValueError(f"Unknown compression case '{case_id}'. Available cases: {available}")


def inspect_compression_case(case: CompressionCase) -> tuple[CompressedContext, dict[str, Any]]:
    context = TextRankCompressor().compress_evidence(
        question=case.question,
        evidence=case.evidence,
        max_sentences=case.max_sentences,
        l1_top_k=case.l1_top_k,
    )
    return context, compression_payload(case, context)


def compression_payload(case: CompressionCase, context: CompressedContext) -> dict[str, Any]:
    quotes = [item.quote for item in case.evidence if item.quote]
    selected_texts = [sentence.text for sentence in context.sentences]
    preserved_quotes = [quote for quote in quotes if quote in selected_texts]
    return {
        "case_id": case.id,
        "question": case.question,
        "learning_note": case.learning_note,
        "max_sentences": case.max_sentences,
        "l1_top_k": case.l1_top_k,
        "original_char_count": context.original_char_count,
        "compressed_char_count": context.compressed_char_count,
        "compression_ratio": context.compression_ratio,
        "expected_quote_count": case.expected_quote_count,
        "preserved_quote_count": len(preserved_quotes),
        "all_quotes_preserved": len(preserved_quotes) == len(quotes),
        "selected_sentences": [
            {
                "text": sentence.text,
                "evidence_id": sentence.evidence_id,
                "source_id": sentence.source_id,
                "score": sentence.score,
                "preserved_quote": sentence.preserved_quote,
            }
            for sentence in context.sentences
        ],
    }


def compression_payload_to_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Compression Trace",
        "",
        f"Case: `{payload['case_id']}`",
        "",
        f"Question: {payload['question']}",
        "",
        f"Max sentences: `{payload['max_sentences']}`",
        f"L1 top-k: `{payload['l1_top_k']}`",
        f"Original chars: `{payload['original_char_count']}`",
        f"Compressed chars: `{payload['compressed_char_count']}`",
        f"Compression ratio: `{payload['compression_ratio']:.3f}`",
        f"Preserved quotes: `{payload['preserved_quote_count']}/{payload['expected_quote_count']}`",
        f"All quotes preserved: `{str(payload['all_quotes_preserved']).lower()}`",
        "",
        "## Learning Note",
        "",
        payload["learning_note"],
        "",
        "## Selected Sentences",
        "",
    ]
    for index, sentence in enumerate(payload["selected_sentences"], start=1):
        lines.extend(
            [
                f"### Sentence {index}",
                "",
                sentence["text"],
                "",
                f"Evidence: `{sentence['evidence_id']}`",
                f"Source: `{sentence['source_id']}`",
                f"Score: `{sentence['score']:.3f}`",
                f"Preserved quote: `{str(sentence['preserved_quote']).lower()}`",
                "",
            ]
        )
    return "\n".join(lines)


def list_compression_cases_markdown(cases: list[CompressionCase]) -> str:
    lines = ["# Compression Cases", ""]
    for case in cases:
        lines.append(
            f"- `{case.id}`: expected quotes `{case.expected_quote_count}` - {case.learning_note}"
        )
    return "\n".join(lines)


def payload_json(payload: dict[str, Any]) -> str:
    return json.dumps(to_jsonable(payload), ensure_ascii=False, indent=2)


def _case_from_raw(raw: dict[str, Any], line_number: int) -> CompressionCase:
    required = {
        "id",
        "question",
        "max_sentences",
        "l1_top_k",
        "evidence",
        "expected_quote_count",
        "learning_note",
    }
    missing = sorted(required - set(raw))
    if missing:
        raise ValueError(f"Compression case line {line_number} is missing fields: {missing}")
    return CompressionCase(
        id=str(raw["id"]),
        question=str(raw["question"]),
        evidence=[Evidence(**item) for item in raw["evidence"]],
        max_sentences=int(raw["max_sentences"]),
        l1_top_k=int(raw["l1_top_k"]),
        expected_quote_count=int(raw["expected_quote_count"]),
        learning_note=str(raw["learning_note"]),
    )
