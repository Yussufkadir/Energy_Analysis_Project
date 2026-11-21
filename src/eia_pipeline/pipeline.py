"""High-level steps. Airflow tasks and the CLI both call these, so the
pipeline can be run and tested without Airflow."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from . import warehouse
from .config import DATASETS, Settings
from .extract import fetch_rows
from .validate import normalize

log = logging.getLogger(__name__)

# EIA revises recent hours and sometimes publishes them late, so every run
# reloads a few days before its own interval. Upserts make this safe.
DEFAULT_LOOKBACK = timedelta(days=3)

# Backfills are loaded in chunks so one failed request doesn't lose a whole year.
CHUNK = timedelta(days=7)


def init(settings: Settings) -> None:
    with warehouse.connect(settings) as conn:
        warehouse.ensure_schema(conn, settings)


def extract_and_load(
    settings: Settings, dataset_name: str, start: datetime, end: datetime
) -> int:
    """Pull [start, end) for one dataset and upsert it. Returns rows changed."""
    dataset = DATASETS[dataset_name]
    api_key = settings.require_api_key()
    changed = 0

    with warehouse.connect(settings) as conn:
        chunk_start = start
        while chunk_start < end:
            chunk_end = min(chunk_start + CHUNK, end)
            raw = fetch_rows(dataset, api_key, chunk_start, chunk_end, settings.respondents)
            rows, report = normalize(raw, dataset)
            changed += warehouse.upsert_rows(conn, dataset, rows, report, chunk_start, chunk_end)
            chunk_start = chunk_end
    return changed


def check(settings: Settings, start: datetime, end: datetime) -> None:
    """Run data-quality checks; raise if any error-severity check fails."""
    with warehouse.connect(settings) as conn:
        results = warehouse.run_checks(conn, settings, start, end)
    failed = [r.name for r in results if not r.passed and r.severity == "error"]
    if failed:
        raise RuntimeError(f"Data quality checks failed: {', '.join(failed)}")


def build_models(settings: Settings) -> None:
    with warehouse.connect(settings) as conn:
        warehouse.build_models(conn, settings)


def export(settings: Settings) -> None:
    with warehouse.connect(settings) as conn:
        warehouse.export_marts(conn, settings)


def run(settings: Settings, start: datetime, end: datetime) -> None:
    """The full pipeline for one window, in the same order as the Airflow DAG."""
    init(settings)
    for name in DATASETS:
        extract_and_load(settings, name, start, end)
    check(settings, start, end)
    build_models(settings)
    export(settings)
