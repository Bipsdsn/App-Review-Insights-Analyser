"""Import normalization — window boundaries, schema, dedupe (offline)."""

from datetime import datetime, timedelta, timezone

import pandas as pd

from src.import_reviews import CANONICAL_COLUMNS, MAX_TEXT_CHARS, _normalize


def _frame(rows):
    base = {
        "platform_id": "id",
        "store": "play",
        "rating": 5,
        "title": "",
        "text": "a perfectly reasonable review text",
        "date": datetime.now(timezone.utc),
    }
    return pd.DataFrame(
        [{**base, **r, "platform_id": f"id{i}"} for i, r in enumerate(rows)]
    )


def _cutoff(weeks):
    return datetime.now(timezone.utc) - timedelta(weeks=weeks)


def test_window_boundary_inclusive_at_8_and_12_weeks():
    for weeks in (8, 12):
        cutoff = _cutoff(weeks)
        df = _frame(
            [
                {"date": cutoff + timedelta(hours=1)},  # just inside
                {"date": cutoff - timedelta(hours=1)},  # just outside
            ]
        )
        out = _normalize(df, cutoff)
        assert len(out) == 1, f"boundary broken at {weeks} weeks"


def test_canonical_schema_and_iso_dates():
    out = _normalize(_frame([{}]), _cutoff(10))
    assert list(out.columns) == CANONICAL_COLUMNS
    assert out["date"].str.match(r"^\d{4}-\d{2}-\d{2}$").all()


def test_invalid_ratings_dropped():
    df = _frame([{"rating": 0}, {"rating": 6}, {"rating": "junk"}, {"rating": 3}])
    out = _normalize(df, _cutoff(10))
    assert len(out) == 1 and out["rating"].iloc[0] == 3


def test_future_dates_and_empty_text_dropped():
    df = _frame(
        [
            {"date": datetime.now(timezone.utc) + timedelta(days=2)},
            {"text": "   "},
            {},
        ]
    )
    out = _normalize(df, _cutoff(10))
    assert len(out) == 1


def test_long_text_truncated():
    df = _frame([{"text": "x" * (MAX_TEXT_CHARS + 500)}])
    out = _normalize(df, _cutoff(10))
    assert len(out["text"].iloc[0]) == MAX_TEXT_CHARS + 1  # + ellipsis


def test_dedupe_on_store_and_review_id():
    df = _frame([{}, {}])
    df["platform_id"] = "same-id"  # same platform id -> same hash
    out = _normalize(df, _cutoff(10))
    merged = out.drop_duplicates(subset=["store", "review_id"])
    assert len(merged) == 1
