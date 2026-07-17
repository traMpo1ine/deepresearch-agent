from __future__ import annotations

import asyncio
import hashlib
import ipaddress
import re
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from io import BytesIO
from urllib.parse import urlparse

from pypdf import PdfReader


USER_AGENT = "deepresearch-agent/0.1 (+https://github.com/traMpo1ine/deepresearch-agent)"
MAX_TEXT_CHARS = 120_000
BLOCKED_HOSTS = {"localhost", "localhost.localdomain"}
TRANSIENT_HTTP_CODES = {408, 425, 429, 500, 502, 503, 504}
INJECTION_PATTERNS = {
    "ignore_previous_instructions": re.compile(
        r"ignore\s+(?:all\s+)?(?:previous|prior)\s+instructions", re.IGNORECASE
    ),
    "system_prompt_request": re.compile(r"system\s+prompt", re.IGNORECASE),
    "role_override": re.compile(r"(?:act|behave)\s+as\s+(?:an?\s+)?", re.IGNORECASE),
    "chinese_instruction_override": re.compile(r"忽略.{0,8}(?:指令|提示词)|系统提示词"),
}


@dataclass(slots=True)
class FetchedPage:
    url: str
    final_url: str
    text: str = ""
    status: str = "error"
    content_type: str = ""
    fetched_at: str = ""
    content_sha256: str = ""
    bytes_read: int = 0
    risk_flags: list[str] = field(default_factory=list)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.status == "ok" and bool(self.text)


class WebPageFetcher:
    """Bounded public-web fetcher with HTML/PDF extraction and SSRF safeguards."""

    def __init__(
        self,
        timeout_seconds: float = 20.0,
        max_bytes: int = 5_000_000,
        max_retries: int = 1,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_bytes = max(1, max_bytes)
        self.max_retries = max(0, max_retries)

    async def fetch(self, url: str) -> FetchedPage:
        validation_error = await asyncio.to_thread(validate_public_url, url)
        if validation_error:
            return _failure(url, "blocked_url", validation_error)
        last_result = _failure(url, "error", "fetch_not_started")
        for attempt in range(self.max_retries + 1):
            last_result = await asyncio.to_thread(self._fetch_once, url)
            if last_result.ok or last_result.status not in {"network_error", "transient_http"}:
                return last_result
            if attempt < self.max_retries:
                await asyncio.sleep(0.2 * (2**attempt))
        return last_result

    def _fetch_once(self, url: str) -> FetchedPage:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/pdf,text/plain,application/json;q=0.9,*/*;q=0.1",
            },
            method="GET",
        )
        try:
            with _open_public_url(request, self.timeout_seconds) as response:
                final_url = response.geturl()
                validation_error = validate_public_url(final_url)
                if validation_error:
                    return _failure(url, "blocked_redirect", validation_error, final_url=final_url)
                content_type = response.headers.get_content_type().lower()
                payload = response.read(self.max_bytes + 1)
                if len(payload) > self.max_bytes:
                    return _failure(
                        url,
                        "too_large",
                        f"response_exceeded_{self.max_bytes}_bytes",
                        final_url=final_url,
                        content_type=content_type,
                        bytes_read=len(payload),
                    )
                text = extract_readable_text(payload, content_type)
                if not text:
                    return _failure(
                        url,
                        "unsupported_or_empty",
                        f"no_readable_text_for_{content_type or 'unknown_content_type'}",
                        final_url=final_url,
                        content_type=content_type,
                        bytes_read=len(payload),
                    )
                text = normalize_web_text(text)
                return FetchedPage(
                    url=url,
                    final_url=final_url,
                    text=text,
                    status="ok",
                    content_type=content_type,
                    fetched_at=_utc_now(),
                    content_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                    bytes_read=len(payload),
                    risk_flags=detect_prompt_injection(text),
                )
        except urllib.error.HTTPError as exc:
            status = "transient_http" if exc.code in TRANSIENT_HTTP_CODES else "http_error"
            return _failure(url, status, f"http_{exc.code}")
        except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
            return _failure(url, "network_error", type(exc).__name__)
        except (OSError, ValueError) as exc:
            return _failure(url, "parse_error", type(exc).__name__)


class _ReadableHTMLParser(HTMLParser):
    SKIP_TAGS = {"script", "style", "noscript", "svg", "canvas", "form", "nav", "footer"}
    BLOCK_TAGS = {
        "article",
        "br",
        "div",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "li",
        "main",
        "p",
        "section",
        "table",
        "td",
        "th",
        "tr",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.SKIP_TAGS:
            self.skip_depth += 1
        elif tag in self.BLOCK_TAGS and self.skip_depth == 0:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIP_TAGS and self.skip_depth > 0:
            self.skip_depth -= 1
        elif tag in self.BLOCK_TAGS and self.skip_depth == 0:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.skip_depth == 0 and data.strip():
            self.parts.append(data)


class _SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validation_error = validate_public_url(newurl)
        if validation_error:
            raise urllib.error.HTTPError(
                newurl,
                403,
                f"blocked_redirect:{validation_error}",
                headers,
                fp,
            )
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def validate_public_url(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return "only_http_and_https_are_allowed"
    hostname = (parsed.hostname or "").rstrip(".").lower()
    if not hostname:
        return "missing_hostname"
    if hostname in BLOCKED_HOSTS or hostname.endswith(".local"):
        return "local_hostname_is_not_allowed"
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(hostname, None)}
    except socket.gaierror:
        return "hostname_resolution_failed"
    if not addresses:
        return "hostname_resolution_failed"
    for address in addresses:
        ip = ipaddress.ip_address(address.split("%", maxsplit=1)[0])
        if not ip.is_global:
            return "private_or_non_global_address_is_not_allowed"
    return None


def _open_public_url(request: urllib.request.Request, timeout_seconds: float):
    opener = urllib.request.build_opener(_SafeRedirectHandler())
    return opener.open(request, timeout=timeout_seconds)


def extract_readable_text(payload: bytes, content_type: str) -> str:
    normalized_type = content_type.lower().split(";", maxsplit=1)[0].strip()
    if normalized_type == "application/pdf" or payload.startswith(b"%PDF"):
        reader = PdfReader(BytesIO(payload))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    if normalized_type in {"text/html", "application/xhtml+xml", ""}:
        parser = _ReadableHTMLParser()
        parser.feed(_decode_text(payload))
        return "".join(parser.parts)
    if normalized_type.startswith("text/") or normalized_type in {
        "application/json",
        "application/xml",
        "application/atom+xml",
    }:
        return _decode_text(payload)
    return ""


def normalize_web_text(text: str, max_chars: int = MAX_TEXT_CHARS) -> str:
    text = text.replace("\x00", " ")
    lines = []
    for line in text.splitlines():
        normalized = re.sub(r"\s+", " ", line).strip()
        if normalized:
            lines.append(normalized)
    return "\n".join(lines)[:max_chars]


def detect_prompt_injection(text: str) -> list[str]:
    sample = text[:20_000]
    return [name for name, pattern in INJECTION_PATTERNS.items() if pattern.search(sample)]


def _decode_text(payload: bytes) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gb18030", "latin-1"):
        try:
            return payload.decode(encoding)
        except UnicodeDecodeError:
            continue
    return payload.decode("utf-8", errors="replace")


def _failure(
    url: str,
    status: str,
    error: str,
    *,
    final_url: str | None = None,
    content_type: str = "",
    bytes_read: int = 0,
) -> FetchedPage:
    return FetchedPage(
        url=url,
        final_url=final_url or url,
        status=status,
        content_type=content_type,
        fetched_at=_utc_now(),
        bytes_read=bytes_read,
        error=error,
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
