from datetime import datetime, timezone

from eia_pipeline.config import GENERATION, REGION
from eia_pipeline.validate import normalize, parse_period


def row(period="2024-07-01T15", respondent="US48", fueltype="NG", value="412345"):
    return {
        "period": period,
        "respondent": respondent,
        "respondent-name": "United States Lower 48",
        "fueltype": fueltype,
        "type-name": "Natural Gas",
        "value": value,
        "value-units": "megawatthours",
    }


def test_period_is_parsed_as_utc():
    assert parse_period("2024-07-01T15") == datetime(2024, 7, 1, 15, tzinfo=timezone.utc)


def test_valid_rows_are_normalized():
    rows, report = normalize([row()], GENERATION)
    assert report.accepted == 1
    period, respondent, name, series, type_name, value, units = rows[0]
    assert (respondent, series, value) == ("US48", "NG", 412345.0)


def test_duplicates_keep_the_last_value():
    rows, report = normalize([row(value="1"), row(value="2")], GENERATION)
    assert report.duplicates == 1
    assert len(rows) == 1 and rows[0][5] == 2.0


def test_missing_values_stay_null_and_are_counted():
    rows, report = normalize([row(value=None), row(fueltype="SUN", value="")], GENERATION)
    assert report.null_values == 2
    assert [r[5] for r in rows] == [None, None]


def test_bad_rows_are_rejected_with_reason():
    bad = [row(respondent=""), row(period="not-a-date"), {"value": "3"}]
    rows, report = normalize(bad, GENERATION)
    assert rows == []
    assert report.rejected == {"missing_key": 2, "bad_period": 1}


def test_region_dataset_uses_type_column():
    r = {"period": "2024-07-01T15", "respondent": "TEX", "type": "D", "value": "70000"}
    rows, report = normalize([r], REGION)
    assert report.accepted == 1 and rows[0][3] == "D"
