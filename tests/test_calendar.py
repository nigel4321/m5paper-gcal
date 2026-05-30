from unittest.mock import MagicMock

import urequests  # stubbed in conftest

from src import calendar


def test_format_rfc3339():
    assert calendar._format_rfc3339((2026, 5, 30, 9, 5, 3, 0, 0)) == "2026-05-30T09:05:03Z"


def test_quote_encodes_colons():
    assert calendar._quote("2026-05-30T09:00:00Z") == "2026-05-30T09%3A00%3A00Z"


def test_parse_events_timed():
    data = {
        "items": [
            {
                "summary": "Team standup",
                "location": "Google Meet",
                "start": {"dateTime": "2026-05-30T09:00:00+01:00"},
                "end": {"dateTime": "2026-05-30T09:30:00+01:00"},
            }
        ]
    }
    [event] = calendar.parse_events(data)
    assert event["title"] == "Team standup"
    assert event["location"] == "Google Meet"
    assert event["all_day"] is False
    assert event["start"] == "2026-05-30T09:00:00+01:00"
    # Indices used by display.py must still line up with the offset present
    assert event["start"][:10] == "2026-05-30"
    assert event["start"][11:16] == "09:00"


def test_parse_events_all_day():
    data = {"items": [{"summary": "Bank holiday", "start": {"date": "2026-05-31"},
                       "end": {"date": "2026-06-01"}}]}
    [event] = calendar.parse_events(data)
    assert event["all_day"] is True
    assert event["start"] == "2026-05-31"
    assert event["location"] == ""


def test_parse_events_missing_summary():
    data = {"items": [{"start": {"dateTime": "2026-05-30T09:00:00Z"},
                       "end": {"dateTime": "2026-05-30T09:30:00Z"}}]}
    [event] = calendar.parse_events(data)
    assert event["title"] == "(no title)"


def test_parse_events_empty():
    assert calendar.parse_events({}) == []


def test_save_and_load_events_round_trip(tmp_path):
    path = str(tmp_path / "events.json")
    events = [{"title": "Meeting", "start": "2026-05-30T09:00:00Z",
               "end": "2026-05-30T09:30:00Z", "location": "", "all_day": False}]
    calendar.save_events(events, path)
    assert calendar.load_events(path) == events


def test_load_events_missing_returns_none(tmp_path):
    assert calendar.load_events(str(tmp_path / "nope.json")) is None


def _stub_response(status_code, payload):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = payload
    return resp


def test_refresh_access_token_success():
    urequests.post.return_value = _stub_response(200, {"access_token": "abc123"})
    assert calendar.refresh_access_token("cid", "secret", "rtok") == "abc123"
    urequests.post.return_value.close.assert_called_once()


def test_refresh_access_token_http_error():
    urequests.post.return_value = _stub_response(400, {"error": "invalid_grant"})
    try:
        calendar.refresh_access_token("cid", "secret", "rtok")
        assert False, "expected RuntimeError"
    except RuntimeError as e:
        assert "400" in str(e)


def test_get_upcoming_events_builds_request_and_parses():
    payload = {"items": [{"summary": "Meeting", "start": {"dateTime": "2026-05-30T09:00:00Z"},
                          "end": {"dateTime": "2026-05-30T09:30:00Z"}}]}
    urequests.get.return_value = _stub_response(200, payload)
    events = calendar.get_upcoming_events("tok", max_results=5, time_min="2026-05-30T08:00:00Z")
    assert events[0]["title"] == "Meeting"
    url = urequests.get.call_args[0][0]
    assert "maxResults=5" in url
    assert "timeMin=2026-05-30T08%3A00%3A00Z" in url
    headers = urequests.get.call_args[1]["headers"]
    assert headers["Authorization"] == "Bearer tok"
