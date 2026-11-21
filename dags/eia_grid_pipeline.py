"""Daily EIA grid pipeline.

    init_warehouse
        -> load_generation, load_region     (run in parallel)
        -> quality_checks
        -> build_models
        -> export_csv

Each task calls a plain function in `eia_pipeline`; the DAG only decides
order, schedule, retries and the time window. Data moves through Postgres,
not XCom, so tasks pass nothing bigger than a row count to each other.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from airflow.sdk import dag, task

from eia_pipeline import pipeline
from eia_pipeline.config import Settings


def load_window(
    data_interval_start: datetime | None, data_interval_end: datetime | None
) -> tuple[datetime, datetime]:
    """The run's interval plus a lookback for late or revised EIA data.

    Manually triggered runs in Airflow 3 have no data interval, so they load
    the most recent complete day instead.
    """
    if data_interval_end is None:
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        data_interval_start, data_interval_end = today - timedelta(days=1), today
    return data_interval_start - pipeline.DEFAULT_LOOKBACK, data_interval_end


@dag(
    dag_id="eia_grid_pipeline",
    description="Incremental load of EIA hourly US grid data into Postgres, plus marts",
    schedule="@daily",
    start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
    catchup=False,  # history is loaded once with `make backfill`, not 700 DAG runs
    max_active_runs=1,  # build_models rebuilds the mart schema; runs must not overlap
    default_args={
        # EIA publishes with a lag of a few hours, so failures get a slow retry.
        "retries": 3,
        "retry_delay": timedelta(minutes=30),
    },
    tags=["energy", "eia"],
)
def eia_grid_pipeline():
    @task
    def init_warehouse() -> None:
        pipeline.init(Settings())

    @task
    def extract_load(dataset: str, data_interval_start=None, data_interval_end=None) -> int:
        start, end = load_window(data_interval_start, data_interval_end)
        return pipeline.extract_and_load(Settings(), dataset, start, end)

    @task
    def quality_checks(data_interval_start=None, data_interval_end=None) -> None:
        start, end = load_window(data_interval_start, data_interval_end)
        pipeline.check(Settings(), start, end)

    @task
    def build_models() -> None:
        pipeline.build_models(Settings())

    @task
    def export_csv() -> None:
        pipeline.export(Settings())

    loads = [
        extract_load.override(task_id="load_generation")("generation"),
        extract_load.override(task_id="load_region")("region"),
    ]
    init_warehouse() >> loads >> quality_checks() >> build_models() >> export_csv()


eia_grid_pipeline()
