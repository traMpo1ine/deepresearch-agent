from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class StructuredParseResult:
    """Result of parsing LLM structured output with fallback metadata."""

    ok: bool
    data: dict[str, Any]
    parse_level: int
    error: str | None = None
    warnings: list[str] = field(default_factory=list)

    def metadata(self) -> dict[str, Any]:
        return {
            "parse_ok": self.ok,
            "parse_level": self.parse_level,
            "parse_error": self.error,
            "parse_warnings": list(self.warnings),
        }


class StructuredOutputParser:
    """Three-level parser for JSON-like LLM outputs.

    Level 1: strict JSON.
    Level 2: fenced JSON or substring JSON extraction.
    Level 3: common repair plus schema defaults.
    """

    def parse(
        self,
        text: str,
        schema_defaults: dict[str, Any] | None = None,
    ) -> StructuredParseResult:
        defaults = dict(schema_defaults or {})
        level1 = self._loads(text)
        if level1 is not None:
            return self._with_schema(level1, defaults, parse_level=1)

        for candidate in self._extract_candidates(text):
            parsed = self._loads(candidate)
            if parsed is not None:
                return self._with_schema(parsed, defaults, parse_level=2)

        for candidate in self._extract_candidates(text) or [text]:
            repaired = self._repair_common_json(candidate)
            parsed = self._loads(repaired)
            if parsed is not None:
                return self._with_schema(
                    parsed,
                    defaults,
                    parse_level=3,
                    warning="Applied common JSON repair.",
                )

        if defaults:
            return StructuredParseResult(
                ok=True,
                data=defaults,
                parse_level=3,
                warnings=["Used schema defaults after parse failure."],
            )
        return StructuredParseResult(
            ok=False,
            data={},
            parse_level=0,
            error="Unable to parse structured output as JSON.",
        )

    def _with_schema(
        self,
        data: Any,
        defaults: dict[str, Any],
        parse_level: int,
        warning: str | None = None,
    ) -> StructuredParseResult:
        if not isinstance(data, dict):
            return StructuredParseResult(
                ok=False,
                data={},
                parse_level=parse_level,
                error=f"Parsed JSON is {type(data).__name__}, expected object.",
            )
        result = dict(data)
        warnings: list[str] = []
        if warning:
            warnings.append(warning)
        missing = [key for key in defaults if key not in result]
        for key in missing:
            result[key] = defaults[key]
        if missing:
            warnings.append(f"Filled missing schema fields: {', '.join(missing)}.")
            parse_level = max(parse_level, 3)
        return StructuredParseResult(ok=True, data=result, parse_level=parse_level, warnings=warnings)

    def _loads(self, text: str) -> Any | None:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    def _extract_candidates(self, text: str) -> list[str]:
        candidates: list[str] = []
        fenced = re.findall(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
        candidates.extend(item.strip() for item in fenced if item.strip())
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidates.append(text[start : end + 1])
        return candidates

    def _repair_common_json(self, text: str) -> str:
        repaired = text.strip()
        repaired = re.sub(r",\s*([}\]])", r"\1", repaired)
        repaired = repaired.replace("'", '"')
        repaired = re.sub(r"([{,]\s*)([A-Za-z_][A-Za-z0-9_-]*)(\s*:)", r'\1"\2"\3', repaired)
        return repaired
