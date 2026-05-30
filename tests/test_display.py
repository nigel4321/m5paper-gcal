from src import display
from src.mock_data import MOCK_EVENTS


def test_day_of_week_known_dates():
    # 0=Sunday .. 6=Saturday
    assert display.day_of_week(2026, 5, 30) == 6  # Saturday
    assert display.day_of_week(2026, 5, 31) == 0  # Sunday
    assert display.day_of_week(2026, 6, 1) == 1   # Monday


def test_format_date_heading():
    assert display.format_date_heading("2026-05-30") == "Saturday 30 May"
    assert display.format_date_heading("2026-06-01") == "Monday 1 June"


def test_format_time():
    assert display.format_time("2026-05-30T09:00:00") == "09:00"


def test_format_duration():
    assert display.format_duration("2026-05-30T09:00:00", "2026-05-30T09:30:00") == "30 min"
    assert display.format_duration("2026-05-30T11:00:00", "2026-05-30T12:00:00") == "1 hr"
    assert display.format_duration("2026-05-30T09:00:00", "2026-05-30T10:45:00") == "1 hr 45 min"


def test_format_duration_across_midnight():
    assert display.format_duration("2026-05-30T23:30:00", "2026-05-31T00:30:00") == "1 hr"


def test_truncate():
    assert display.truncate("short", 10) == "short"
    assert display.truncate("a much longer string", 10) == "a much lo…"
    assert len(display.truncate("a much longer string", 10)) == 10


def test_format_detail_line_location_and_duration():
    event = {
        "start": "2026-05-30T09:00:00",
        "end": "2026-05-30T09:30:00",
        "location": "Google Meet",
        "all_day": False,
    }
    assert display.format_detail_line(event) == "Google Meet · 30 min"


def test_format_detail_line_no_location():
    event = {
        "start": "2026-05-31T10:00:00",
        "end": "2026-05-31T10:45:00",
        "location": "",
        "all_day": False,
    }
    assert display.format_detail_line(event) == "45 min"


def test_format_detail_line_all_day_is_empty():
    event = {"start": "2026-05-31", "end": "2026-05-31", "location": "", "all_day": True}
    assert display.format_detail_line(event) == ""


def test_group_events_by_day_preserves_order_and_splits_days():
    groups = display.group_events_by_day(MOCK_EVENTS)
    assert [date for date, _ in groups] == ["2026-05-30", "2026-05-31", "2026-06-01"]
    assert len(groups[0][1]) == 2  # two events on 30 May
    assert len(groups[1][1]) == 2  # all-day + 1:1 on 31 May
    assert len(groups[2][1]) == 1


def test_render_all_runs_with_stubbed_device():
    # M5 is stubbed in conftest; this exercises the full render path for crashes.
    display.render_all(MOCK_EVENTS, 84, "09:15")
