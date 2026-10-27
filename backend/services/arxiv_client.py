"""Small, conservative client for the official arXiv Atom API."""

from __future__ import annotations

import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone

from backend.app.config import (
    ARXIV_API_TIMEOUT_SECONDS,
    ARXIV_API_URL,
    ARXIV_PAGE_SIZE,
    ARXIV_REQUEST_INTERVAL_SECONDS,
)

ATOM = "{http://www.w3.org/2005/Atom}"
OPENSEARCH = "{http://a9.com/-/spec/opensearch/1.1/}"
_CATEGORY_RE = re.compile(r"^[a-z][a-z0-9-]*(?:\.[A-Za-z0-9-]+)?$")
SORT_BY_VALUES = {"relevance", "lastUpdatedDate", "submittedDate"}
SORT_ORDER_VALUES = {"ascending", "descending"}


class ArxivClientError(RuntimeError):
    pass


@dataclass(frozen=True)
class ArxivPaper:
    arxiv_id: str
    title: str
    abstract: str
    authors: str
    submitted_at: datetime
    updated_at: datetime
    categories: list[str]
    url: str


def validate_categories(categories: list[str]) -> list[str]:
    normalized = sorted({category.strip() for category in categories if category.strip()})
    if not normalized or any(not _CATEGORY_RE.fullmatch(category) for category in normalized):
        raise ValueError("categories must contain valid arXiv category names")
    return normalized


def build_search_query(categories: list[str], start: datetime | None = None, end: datetime | None = None) -> str:
    category_query = " OR ".join(f"cat:{category}" for category in validate_categories(categories))
    query = f"({category_query})"
    if start is not None or end is not None:
        low = _format_query_date(start or datetime(1990, 1, 1, tzinfo=timezone.utc))
        high = _format_query_date(end or datetime.now(timezone.utc))
        query += f" AND submittedDate:[{low} TO {high}]"
    return query


def _format_query_date(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y%m%d%H%M")


def _clean(value: str | None) -> str:
    return " ".join((value or "").split())


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.strip().replace("Z", "+00:00")).astimezone(timezone.utc)


def parse_atom(xml: bytes | str) -> tuple[list[ArxivPaper], int | None]:
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as exc:
        raise ArxivClientError("arXiv returned malformed XML") from exc
    papers: list[ArxivPaper] = []
    for entry in root.findall(f"{ATOM}entry"):
        identifier = _clean(entry.findtext(f"{ATOM}id"))
        match = re.search(r"/abs/(.+?)(?:v\d+)?$", identifier)
        if not match:
            continue
        arxiv_id = re.sub(r"v\d+$", "", match.group(1))
        authors = ", ".join(_clean(node.findtext(f"{ATOM}name")) for node in entry.findall(f"{ATOM}author"))
        links = entry.findall(f"{ATOM}link")
        url = next((link.attrib.get("href", "") for link in links if link.attrib.get("rel") == "alternate"), identifier)
        papers.append(ArxivPaper(
            arxiv_id=arxiv_id,
            title=_clean(entry.findtext(f"{ATOM}title")),
            abstract=_clean(entry.findtext(f"{ATOM}summary")),
            authors=authors,
            submitted_at=_parse_datetime(_clean(entry.findtext(f"{ATOM}published"))),
            updated_at=_parse_datetime(_clean(entry.findtext(f"{ATOM}updated"))),
            categories=[node.attrib["term"] for node in entry.findall(f"{ATOM}category") if node.attrib.get("term")],
            url=url.replace("http://", "https://", 1),
        ))
    total_text = root.findtext(f"{OPENSEARCH}totalResults")
    return papers, int(total_text) if total_text and total_text.isdigit() else None


class ArxivClient:
    def __init__(self, url: str = ARXIV_API_URL, timeout: float = ARXIV_API_TIMEOUT_SECONDS, interval: float = ARXIV_REQUEST_INTERVAL_SECONDS):
        self.url = url
        self.timeout = timeout
        self.interval = interval
        self._last_request: float | None = None

    def fetch_page(self, categories: list[str], start: int = 0, max_results: int = ARXIV_PAGE_SIZE, submitted_after: datetime | None = None, submitted_before: datetime | None = None, sort_by: str = "submittedDate", sort_order: str = "ascending") -> tuple[list[ArxivPaper], int | None]:
        if sort_by not in SORT_BY_VALUES:
            raise ValueError(f"Unsupported arXiv sort_by: {sort_by}")
        if sort_order not in SORT_ORDER_VALUES:
            raise ValueError(f"Unsupported arXiv sort_order: {sort_order}")
        if self._last_request is not None:
            time.sleep(max(0.0, self.interval - (time.monotonic() - self._last_request)))
        params = {"search_query": build_search_query(categories, submitted_after, submitted_before), "start": str(start), "max_results": str(min(max_results, 2000)), "sortBy": sort_by, "sortOrder": sort_order}
        request = urllib.request.Request(f"{self.url}?{urllib.parse.urlencode(params)}", headers={"User-Agent": "Primrose/1.0 (research corpus client)"})
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    body = response.read()
                self._last_request = time.monotonic()
                return parse_atom(body)
            except urllib.error.HTTPError as exc:
                last_error = exc
                if exc.code not in (429, 500, 502, 503, 504) or attempt == 2:
                    break
                retry_after = exc.headers.get("Retry-After")
                delay = float(retry_after) if retry_after and retry_after.isdigit() else self.interval * (attempt + 1)
                time.sleep(delay)
            except (urllib.error.URLError, TimeoutError) as exc:
                last_error = exc
                if attempt == 2:
                    break
                time.sleep(self.interval * (attempt + 1))
        self._last_request = time.monotonic()
        raise ArxivClientError(f"arXiv request failed: {last_error}") from last_error

