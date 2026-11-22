"""Integration test against a real Postgres. Skipped unless TEST_WAREHOUSE_DSN is set.

WARNING: the fixture drops and recreates every warehouse schema. Point it at
a throwaway database, never at the one holding your loaded data:

    docker compose exec warehouse createdb -U energy energy_test
    TEST_WAREHOUSE_DSN=postgresql://energy:energy@localhost:5433/energy_test pytest
"""

import os
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from eia_pipeline import warehouse
from eia_pipeline.config import GENERATION, REGION, Settings
from eia_pipeline.validate import normalize

DSN = os.environ.get("TEST_WAREHOUSE_DSN")
pytestmark = pytest.mark.skipif(not DSN, reason="TEST_WAREHOUSE_DSN not set")

# Refuse to wipe the main warehouse (local `energy` DB) by accident; CI uses its own server.
if DSN and DSN.rstrip("/").endswith(":5433/energy"):
    raise RuntimeError("TEST_WAREHOUSE_DSN points at the main warehouse; use energy_test")

START = datetime(2024, 7, 1, tzinfo=timezone.utc)
END = START + timedelta(days=2)
FUELS = {"NG": 0.45, "COL": 0.15, "NUC": 0.19, "WND": 0.11, "SUN": 0.07, "WAT": 0.03}


def synthetic_rows(demand_scale=1.0):
    gen, region = [], []
    hour = START
    while hour < END:
        period = hour.strftime("%Y-%m-%dT%H")
        demand = 500_000 * demand_scale
        for code, share in FUELS.items():
            gen.append({"period": period, "respondent": "US48", "fueltype": code,
                        "value": str(demand * share)})
        for typ, value in {"D": demand, "DF": demand * 1.02, "NG": demand, "TI": 0}.items():
            region.append({"period": period, "respondent": "US48", "type": typ,
                           "value": str(value)})
        hour += timedelta(hours=1)
    # one missing solar hour, which must stay missing (not filled with an average)
    gen[5]["value"] = None
    return gen, region


@pytest.fixture
def settings(tmp_path):
    s = replace(Settings(), warehouse_dsn=DSN, export_dir=tmp_path)
    with warehouse.connect(s) as conn:
        conn.execute("drop schema if exists raw, meta, ref, staging, mart cascade")
        warehouse.ensure_schema(conn, s)
    return s


def load(conn, gen, region):
    for dataset, raw in ((GENERATION, gen), (REGION, region)):
        rows, report = normalize(raw, dataset)
        warehouse.upsert_rows(conn, dataset, rows, report, START, END)


def test_full_pipeline_is_idempotent_and_correct(settings):
    gen, region = synthetic_rows()
    with warehouse.connect(settings) as conn:
        load(conn, gen, region)
        load(conn, gen, region)  # re-running the same window must not duplicate
        n = conn.execute("select count(*) from raw.fuel_type_hourly").fetchone()[0]
        assert n == 48 * len(FUELS)

        # a revised value replaces the old one
        revised_gen, revised_region = synthetic_rows(demand_scale=1.1)
        load(conn, revised_gen, revised_region)
        demand = conn.execute(
            "select value from raw.region_hourly where type = 'D' limit 1").fetchone()[0]
        assert demand == pytest.approx(550_000)

        results = warehouse.run_checks(conn, settings, START, END)
        assert all(r.passed for r in results if r.severity == "error"), results

        warehouse.build_models(conn, settings)

        nulls = conn.execute(
            "select count(*) from raw.fuel_type_hourly where value is null").fetchone()[0]
        assert nulls == 1

        mape = conn.execute(
            "select avg(forecast_mape_pct) from mart.daily_demand").fetchone()[0]
        assert float(mape) == pytest.approx(100 * 0.02 / 1.0, rel=0.05)

        share = conn.execute(
            "select avg(share_pct) from mart.daily_fuel_mix where fuel_code = 'NG'").fetchone()[0]
        assert 44 < float(share) < 47

        hours = conn.execute(
            "select min(hours_reported) from mart.daily_fuel_mix where fuel_code = 'SUN'"
        ).fetchone()[0]
        assert hours < 24  # the missing hour is visible, not filled

        paths = warehouse.export_marts(conn, settings)
    assert {p.name for p in paths} == {f"{t}.csv" for t in warehouse.MART_TABLES}
    assert all(p.stat().st_size > 0 for p in paths)


def test_implausible_demand_fails_checks(settings):
    gen, region = synthetic_rows(demand_scale=5)  # 2,500 GW: impossible
    with warehouse.connect(settings) as conn:
        load(conn, gen, region)
        results = {r.name: r for r in warehouse.run_checks(conn, settings, START, END)}
    assert not results["us48_demand_plausible"].passed
