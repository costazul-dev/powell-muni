from datetime import datetime, timedelta, timezone

from display.layout import (
    Row,
    build_row,
    build_rows,
    format_times,
    is_stale,
    minutes_until,
    next_minutes,
)
from transit.parse import Arrival

NOW = datetime(2026, 11, 9, 8, 0, 0, tzinfo=timezone(timedelta(hours=-8)))
ROW_45 = {"line": "45", "stop_code": "15678", "color": "blue"}
MAX_AGE = 432  # 2 * fetch_interval_seconds(3, 50)


def arrival(line: str, minutes: float, stop_code: str = "15678") -> Arrival:
    return Arrival(line=line, stop_code=stop_code, expected=NOW + timedelta(minutes=minutes))


def test_minutes_until_rounds_down():
    assert minutes_until(NOW + timedelta(minutes=3, seconds=59), NOW) == 3


def test_minutes_until_exact_minute():
    assert minutes_until(NOW + timedelta(minutes=11), NOW) == 11


def test_next_minutes_filters_by_line_drops_past_sorts_and_caps():
    arrivals = [
        arrival("45", 24),
        arrival("1", 2),
        arrival("45", -1),
        arrival("45", 3),
        arrival("45", 30),
        arrival("45", 11),
    ]
    assert next_minutes(arrivals, "45", NOW) == [3, 11, 24]


def test_next_minutes_respects_limit():
    arrivals = [arrival("45", 3), arrival("45", 11), arrival("45", 24)]
    assert next_minutes(arrivals, "45", NOW, limit=2) == [3, 11]


def test_next_minutes_keeps_arriving_now():
    assert next_minutes([arrival("45", 0.5)], "45", NOW) == [0]


def test_is_stale_when_never_fetched():
    assert is_stale(None, NOW, MAX_AGE)


def test_is_stale_false_when_fresh():
    assert not is_stale(NOW - timedelta(seconds=60), NOW, MAX_AGE)


def test_is_stale_true_when_expired():
    assert is_stale(NOW - timedelta(seconds=MAX_AGE + 1), NOW, MAX_AGE)


def test_format_times_populated():
    assert format_times([3, 11, 24]) == "3, 11, 24"


def test_format_times_empty():
    assert format_times([]) == "--"


def test_build_row_fresh_data_is_white():
    row = build_row(ROW_45, [arrival("45", 3), arrival("45", 11)], NOW, NOW, MAX_AGE)
    assert row == Row(line="45", badge_color="blue", text="3, 11", text_color="white")


def test_build_row_stale_data_is_yellow():
    last_success = NOW - timedelta(seconds=MAX_AGE + 1)
    row = build_row(ROW_45, [arrival("45", 3)], last_success, NOW, MAX_AGE)
    assert row.text == "3"
    assert row.text_color == "yellow"


def test_build_row_no_arrivals_is_yellow_dashes():
    row = build_row(ROW_45, [arrival("1", 3)], NOW, NOW, MAX_AGE)
    assert row.text == "--"
    assert row.text_color == "yellow"


def test_build_rows_maps_each_row_to_its_stop():
    rows_config = [ROW_45, {"line": "T", "stop_code": "17166", "color": "red"}]
    arrivals_by_stop = {"15678": [arrival("45", 5)]}
    last_success_by_stop = {"15678": NOW, "17166": None}
    rows = build_rows(rows_config, arrivals_by_stop, last_success_by_stop, NOW, MAX_AGE)
    assert rows == [
        Row(line="45", badge_color="blue", text="5", text_color="white"),
        Row(line="T", badge_color="red", text="--", text_color="yellow"),
    ]
