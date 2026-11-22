"""Row-level validation and normalisation before anything touches the warehouse.

Deliberately *not* done here: filling missing values. The original notebook
replaced every missing value with the global mean across all fuel types and
regions, which wrote e.g. a typical gas-plant hour into a solar series at
midnight. Missing hours stay NULL in the warehouse; the marts report
completeness instead, so the gaps stay visible.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .config import Dataset

NormalizedRow = tuple[datetime, str, str | None, str, str | None, float | None, str | None]


@dataclass
class ValidationReport:
    received: int = 0
    accepted: int = 0
    duplicates: int = 0
    null_values: int = 0
    rejected: dict[str, int] = field(default_factory=dict)

    def reject(self, reason: str) -> None:
        self.rejected[reason] = self.rejected.get(reason, 0) + 1

    @property
    def rejected_total(self) -> int:
        return sum(self.rejected.values())


def parse_period(raw: str) -> datetime:
    """EIA hourly periods look like '2024-01-31T23' and are in UTC."""
    return datetime.strptime(raw, "%Y-%m-%dT%H").replace(tzinfo=timezone.utc)


def parse_value(raw: object) -> float | None:
    if raw is None or raw == "":
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def normalize(
    rows: Iterable[dict], dataset: Dataset
) -> tuple[list[NormalizedRow], ValidationReport]:
    """Validate raw API rows and return (unique rows, report).

    Duplicates on the natural key (period, respondent, series) keep the last
    occurrence, matching the warehouse's upsert behaviour.
    """
    report = ValidationReport()
    series_col = dataset.series_column
    unique: dict[tuple[datetime, str, str], NormalizedRow] = {}

    for row in rows:
        report.received += 1

        respondent = row.get("respondent")
        series = row.get(series_col)
        if not respondent or not series:
            report.reject("missing_key")
            continue
        try:
            period = parse_period(row["period"])
        except (KeyError, TypeError, ValueError):
            report.reject("bad_period")
            continue

        value = parse_value(row.get("value"))
        if value is None:
            report.null_values += 1

        key = (period, respondent, series)
        if key in unique:
            report.duplicates += 1
        unique[key] = (
            period,
            respondent,
            row.get("respondent-name"),
            series,
            row.get("type-name"),
            value,
            row.get("value-units"),
        )

    report.accepted = len(unique)
    return list(unique.values()), report
