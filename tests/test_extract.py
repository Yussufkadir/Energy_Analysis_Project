from datetime import datetime, timezone

import pytest

from eia_pipeline.config import GENERATION
from eia_pipeline.extract import build_params, fetch_rows

START = datetime(2024, 1, 1, tzinfo=timezone.utc)
END = datetime(2024, 1, 2, tzinfo=timezone.utc)


def test_end_is_converted_to_eia_inclusive_hour():
    params = build_params(GENERATION, "key", START, END, offset=0)
    assert params["start"] == "2024-01-01T00"
    assert params["end"] == "2024-01-01T23"


def test_sort_covers_the_full_natural_key_for_stable_paging():
    params = build_params(GENERATION, "key", START, END, offset=0)
    sort_cols = [params[f"sort[{i}][column]"] for i in range(3)]
    assert sort_cols == ["period", "respondent", "fueltype"]


def test_respondent_filter_becomes_facets():
    params = build_params(GENERATION, "key", START, END, 0, respondents=("US48", "TEX"))
    assert params["facets[respondent][0]"] == "US48"
    assert params["facets[respondent][1]"] == "TEX"


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def raise_for_status(self):
        pass

    def json(self):
        return self.body


class FakeSession:
    """Serves `total` rows in pages of `page` rows and records the offsets asked for."""

    def __init__(self, total, page):
        self.total, self.page, self.offsets = total, page, []

    def get(self, url, params, timeout):
        offset = params["offset"]
        self.offsets.append(offset)
        n = max(0, min(self.page, self.total - offset))
        data = [{"i": offset + k} for k in range(n)]
        return FakeResponse({"response": {"total": str(self.total), "data": data}})


def test_paginates_until_total_is_reached():
    session = FakeSession(total=12, page=5)
    rows = list(fetch_rows(GENERATION, "key", START, END, session=session))
    assert [r["i"] for r in rows] == list(range(12))
    assert session.offsets == [0, 5, 10]


def test_empty_window_makes_one_request():
    session = FakeSession(total=0, page=5)
    assert list(fetch_rows(GENERATION, "key", START, END, session=session)) == []
    assert session.offsets == [0]


def test_rejects_inverted_window():
    with pytest.raises(ValueError):
        list(fetch_rows(GENERATION, "key", END, START, session=FakeSession(0, 5)))
