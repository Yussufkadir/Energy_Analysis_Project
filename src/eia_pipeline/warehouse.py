"""Everything that talks to Postgres: schema setup, loads, models, checks, exports."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import psycopg

from .config import Dataset, Settings
from .validate import NormalizedRow, ValidationReport

log = logging.getLogger(__name__)

MART_TABLES = (
    "daily_fuel_mix",
    "hourly_profile",
    "daily_demand",
    "monthly_summary",
    "data_completeness",
)


def connect(settings: Settings) -> psycopg.Connection:
    # autocommit so every `conn.transaction()` block is a real, committed
    # transaction instead of a savepoint inside one long implicit transaction.
    return psycopg.connect(settings.warehouse_dsn, autocommit=True)


def _run_sql_files(conn: psycopg.Connection, folder: Path) -> None:
    files = sorted(folder.glob("*.sql"))
    if not files:
        raise FileNotFoundError(f"No .sql files in {folder}")
    with conn.transaction():
        for path in files:
            log.info("Running %s", path.name)
            conn.execute(path.read_text())


def ensure_schema(conn: psycopg.Connection, settings: Settings) -> None:
    """Create raw/meta/ref tables if missing. Safe to run on every pipeline run."""
    _run_sql_files(conn, settings.sql_dir / "schema")


def build_models(conn: psycopg.Connection, settings: Settings) -> None:
    """Rebuild staging views and mart tables in a single transaction."""
    _run_sql_files(conn, settings.sql_dir / "models")


def upsert_rows(
    conn: psycopg.Connection,
    dataset: Dataset,
    rows: list[NormalizedRow],
    report: ValidationReport,
    window_start: datetime,
    window_end: datetime,
) -> int:
    """COPY rows into a temp table, then upsert into the raw table.

    COPY keeps a year-long backfill (millions of rows) fast; the upsert keeps
    re-runs idempotent and picks up revised values.
    """
    series = dataset.series_column
    columns = f"period, respondent, respondent_name, {series}, type_name, value, value_units"

    with conn.transaction(), conn.cursor() as cur:
        cur.execute(
            f"create temp table staging_load (like {dataset.raw_table} including defaults) "
            "on commit drop"
        )
        with cur.copy(f"copy staging_load ({columns}) from stdin") as copy:
            for row in rows:
                copy.write_row(row)

        cur.execute(
            f"""
            insert into {dataset.raw_table} ({columns}, loaded_at)
            select {columns}, now() from staging_load
            on conflict (period, respondent, {series}) do update set
                respondent_name = excluded.respondent_name,
                type_name       = excluded.type_name,
                value           = excluded.value,
                value_units     = excluded.value_units,
                loaded_at       = excluded.loaded_at
            where {dataset.raw_table}.value is distinct from excluded.value
               or {dataset.raw_table}.respondent_name is distinct from excluded.respondent_name
            """
        )
        changed = cur.rowcount

        cur.execute(
            """
            insert into meta.load_log
                (dataset, window_start, window_end, received, accepted,
                 duplicates, null_values, rejected)
            values (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                dataset.name,
                window_start,
                window_end,
                report.received,
                report.accepted,
                report.duplicates,
                report.null_values,
                report.rejected_total,
            ),
        )

    log.info(
        "%s: %d rows accepted, %d inserted or changed, %d duplicates, %d nulls, rejected=%s",
        dataset.name,
        report.accepted,
        changed,
        report.duplicates,
        report.null_values,
        report.rejected,
    )
    return changed


@dataclass
class CheckResult:
    name: str
    severity: str
    failures: list[tuple]

    @property
    def passed(self) -> bool:
        return not self.failures


def _severity(sql: str) -> str:
    first = sql.lstrip().splitlines()[0].lower()
    return "warn" if "severity: warn" in first else "error"


def run_checks(
    conn: psycopg.Connection, settings: Settings, window_start: datetime, window_end: datetime
) -> list[CheckResult]:
    """Run every sql/checks/*.sql. Each query returns the rows that violate it."""
    params = {"window_start": window_start, "window_end": window_end}
    results = []
    for path in sorted((settings.sql_dir / "checks").glob("*.sql")):
        sql = path.read_text()
        rows = conn.execute(sql, params if "%(" in sql else None).fetchall()
        result = CheckResult(path.stem, _severity(sql), rows)
        level = logging.INFO if result.passed else (
            logging.WARNING if result.severity == "warn" else logging.ERROR
        )
        log.log(level, "check %-40s %s (%d failing rows)", result.name,
                "PASS" if result.passed else result.severity.upper(), len(rows))
        for row in rows[:5]:
            log.log(level, "    %s", row)
        results.append(result)
    return results


def export_marts(conn: psycopg.Connection, settings: Settings) -> list[Path]:
    """Write every mart table to CSV, for Tableau Public (which can't query Postgres)."""
    settings.export_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for table in MART_TABLES:
        path = settings.export_dir / f"{table}.csv"
        with conn.cursor() as cur, path.open("wb") as fh:
            with cur.copy(f"copy (select * from mart.{table}) to stdout with csv header") as copy:
                for chunk in copy:
                    fh.write(chunk)
        log.info("Exported %s", path)
        written.append(path)
    return written
