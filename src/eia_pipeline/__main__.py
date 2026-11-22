"""Command-line entry point, for running or backfilling without Airflow.

    python -m eia_pipeline run --start 2024-01-01 --end 2025-01-01
    python -m eia_pipeline models
    python -m eia_pipeline export
"""

from __future__ import annotations

import argparse
import logging
from datetime import datetime, timezone

from . import pipeline
from .config import Settings


def _date(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def main() -> None:
    parser = argparse.ArgumentParser(prog="eia_pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="extract, load, check, model and export a date range")
    run.add_argument("--start", type=_date, required=True, help="inclusive, YYYY-MM-DD (UTC)")
    run.add_argument("--end", type=_date, required=True, help="exclusive, YYYY-MM-DD (UTC)")

    sub.add_parser("init", help="create warehouse tables")
    sub.add_parser("models", help="rebuild staging views and marts")
    sub.add_parser("export", help="write marts to CSV")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = Settings()

    if args.command == "run":
        pipeline.run(settings, args.start, args.end)
    elif args.command == "init":
        pipeline.init(settings)
    elif args.command == "models":
        pipeline.build_models(settings)
    elif args.command == "export":
        pipeline.export(settings)


if __name__ == "__main__":
    main()
