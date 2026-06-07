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


def test_format_weekday_and_day_month():
    assert display.format_weekday("2026-05-30") == "Saturday"
    assert display.format_day_month("2026-05-30") == "30 May"
    assert display.format_weekday("2026-06-01") == "Monday"
    assert display.format_day_month("2026-06-01") == "1 June"


def test_format_time():
    assert display.format_time("2026-05-30T09:00:00") == "09:00"


def test_truncate():
    assert display.truncate("short", 10) == "short"
    assert display.truncate("a much longer string", 10) == "a much lon"
    assert len(display.truncate("a much longer string", 10)) == 10


def test_group_events_by_day_preserves_order_and_splits_days():
    groups = display.group_events_by_day(MOCK_EVENTS)
    assert [date for date, _ in groups] == ["2026-05-30", "2026-05-31", "2026-06-01"]
    assert len(groups[0][1]) == 2  # two events on 30 May
    assert len(groups[1][1]) == 2  # all-day + 1:1 on 31 May
    assert len(groups[2][1]) == 1


def test_format_temperature():
    assert display.format_temperature(18.4) == "18°C"
    assert display.format_temperature(0.0) == "0°C"
    assert display.format_temperature(-3.7) == "-4°C"


def test_format_clock():
    assert display.format_clock((2026, 5, 30, 9, 5, 0, 0, 0)) == "09:05"
    assert display.format_clock((2026, 5, 30, 14, 30, 0, 0, 0)) == "14:30"


def test_date_str_from_time():
    assert display.date_str_from_time((2026, 6, 4, 18, 23, 0, 0, 0)) == "2026-06-04"


def test_london_offset_winter_and_summer():
    # Mid-January -> GMT
    assert display._london_offset_hours((2026, 1, 15, 12, 0, 0, 0, 0)) == 0
    # Mid-July -> BST
    assert display._london_offset_hours((2026, 7, 15, 12, 0, 0, 0, 0)) == 1


def test_london_offset_dst_transitions_2026():
    # Last Sunday of March 2026 is the 29th; BST starts at 01:00 UTC.
    assert display._london_offset_hours((2026, 3, 29, 0, 59, 0, 0, 0)) == 0  # just before
    assert display._london_offset_hours((2026, 3, 29, 1, 0, 0, 0, 0)) == 1   # at switch
    assert display._london_offset_hours((2026, 3, 30, 12, 0, 0, 0, 0)) == 1
    # Last Sunday of October 2026 is the 25th; GMT resumes at 01:00 UTC.
    assert display._london_offset_hours((2026, 10, 25, 0, 59, 0, 0, 0)) == 1
    assert display._london_offset_hours((2026, 10, 25, 1, 0, 0, 0, 0)) == 0
    assert display._london_offset_hours((2026, 10, 26, 12, 0, 0, 0, 0)) == 0


def test_to_london_adds_bst_offset_and_rolls_day():
    # Winter: no offset
    assert display.to_london((2026, 1, 15, 12, 0, 0, 0, 0))[:6] == (2026, 1, 15, 12, 0, 0)
    # Summer afternoon: +1h
    assert display.to_london((2026, 7, 15, 12, 0, 0, 0, 0))[:6] == (2026, 7, 15, 13, 0, 0)
    # Summer 23:30 UTC -> next day 00:30 BST
    assert display.to_london((2026, 7, 15, 23, 30, 0, 0, 0))[:6] == (2026, 7, 16, 0, 30, 0)
    # Month rollover: 31 July 23:30 UTC -> 1 Aug 00:30 BST
    assert display.to_london((2026, 7, 31, 23, 30, 0, 0, 0))[:6] == (2026, 8, 1, 0, 30, 0)


def test_render_all_runs_with_stubbed_device():
    # M5 is stubbed in conftest; this exercises the full render path for crashes.
    display.render_all(MOCK_EVENTS, 84, "09:15")


def test_render_all_with_warning_runs():
    display.render_all(MOCK_EVENTS, 84, "09:15", warning="update failed")


def test_render_error_runs():
    display.render_error("No WiFi", "Could not connect", 84)
