"""Runtime configuration, read from environment variables (see .env.example)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Dataset:
    """One EIA v2 hourly endpoint and how its rows map onto a raw table."""

    name: str
    route: str
    # The column that, together with period + respondent, identifies a row.
    series_column: str
    raw_table: str


GENERATION = Dataset(
    name="generation",
    route="electricity/rto/fuel-type-data",
    series_column="fueltype",
    raw_table="raw.fuel_type_hourly",
)

REGION = Dataset(
    name="region",
    route="electricity/rto/region-data",
    series_column="type",
    raw_table="raw.region_hourly",
)

DATASETS = {d.name: d for d in (GENERATION, REGION)}


@dataclass(frozen=True)
class Settings:
    api_key: str = field(default_factory=lambda: os.environ.get("EIA_API_KEY", ""))
    warehouse_dsn: str = field(
        default_factory=lambda: os.environ.get(
            "WAREHOUSE_DSN", "postgresql://energy:energy@localhost:5433/energy"
        )
    )
    # Optional comma-separated respondent filter, e.g. "US48,CAL,TEX".
    # Empty means every respondent EIA publishes (~70 balancing authorities).
    respondents: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            r.strip() for r in os.environ.get("EIA_RESPONDENTS", "").split(",") if r.strip()
        )
    )
    export_dir: Path = field(
        default_factory=lambda: Path(os.environ.get("EXPORT_DIR", PROJECT_ROOT / "exports"))
    )
    sql_dir: Path = field(
        default_factory=lambda: Path(os.environ.get("SQL_DIR", PROJECT_ROOT / "sql"))
    )

    def require_api_key(self) -> str:
        if not self.api_key:
            raise RuntimeError(
                "EIA_API_KEY is not set. Get a free key at https://www.eia.gov/opendata/ "
                "and put it in your .env file."
            )
        return self.api_key
