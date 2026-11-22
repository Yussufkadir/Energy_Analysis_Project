"""Paginated, retrying extraction from the EIA v2 API.

Compared with the original notebook this:
  * pulls an explicit [start, end) window instead of a whole year, so daily runs
    fetch only a few thousand rows instead of taking ~1.5 hours;
  * sorts on the full natural key, so offset paging is stable (sorting on
    `period` alone lets rows with the same timestamp shuffle between pages,
    which silently duplicates some rows and drops others);
  * retries transient HTTP failures with backoff instead of giving up.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from datetime import datetime, timedelta

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import Dataset

log = logging.getLogger(__name__)

API_BASE = "https://api.eia.gov/v2"
PAGE_SIZE = 5000  # EIA's maximum rows per request


def build_session() -> requests.Session:
    retry = Retry(
        total=5,
        backoff_factor=2,  # 2s, 4s, 8s, ...
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def eia_hour(ts: datetime) -> str:
    """Format a timestamp the way EIA's hourly endpoints expect: 2024-01-31T23."""
    return ts.strftime("%Y-%m-%dT%H")


def build_params(
    dataset: Dataset,
    api_key: str,
    start: datetime,
    end: datetime,
    offset: int,
    respondents: tuple[str, ...] = (),
) -> dict[str, str | int]:
    """Query parameters for one page. `end` is exclusive; EIA's `end` is inclusive."""
    params: dict[str, str | int] = {
        "api_key": api_key,
        "frequency": "hourly",
        "data[0]": "value",
        "start": eia_hour(start),
        "end": eia_hour(end - timedelta(hours=1)),
        "sort[0][column]": "period",
        "sort[0][direction]": "asc",
        "sort[1][column]": "respondent",
        "sort[1][direction]": "asc",
        "sort[2][column]": dataset.series_column,
        "sort[2][direction]": "asc",
        "offset": offset,
        "length": PAGE_SIZE,
    }
    for i, respondent in enumerate(respondents):
        params[f"facets[respondent][{i}]"] = respondent
    return params


def fetch_rows(
    dataset: Dataset,
    api_key: str,
    start: datetime,
    end: datetime,
    respondents: tuple[str, ...] = (),
    session: requests.Session | None = None,
) -> Iterator[dict]:
    """Yield raw API rows for [start, end), one page at a time."""
    if end <= start:
        raise ValueError(f"end ({end}) must be after start ({start})")

    session = session or build_session()
    url = f"{API_BASE}/{dataset.route}/data/"
    offset = 0
    total: int | None = None

    while True:
        params = build_params(dataset, api_key, start, end, offset, respondents)
        resp = session.get(url, params=params, timeout=60)
        resp.raise_for_status()
        body = resp.json()
        if "response" not in body:
            raise RuntimeError(f"Unexpected EIA response: {str(body)[:500]}")

        page = body["response"].get("data", [])
        if total is None:
            total = int(body["response"].get("total", 0))
            log.info("%s %s..%s: %d rows to fetch", dataset.name, start, end, total)

        yield from page
        offset += len(page)
        if not page or offset >= total:
            break

    log.info("%s: fetched %d rows", dataset.name, offset)
