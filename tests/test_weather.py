from unittest.mock import MagicMock

import requests  # stubbed in conftest

from src import weather


def test_code_to_icon_known_buckets_day():
    assert weather.code_to_icon(0) == "01d"
    assert weather.code_to_icon(1) == "02d"
    assert weather.code_to_icon(3) == "04d"
    assert weather.code_to_icon(45) == "50d"
    assert weather.code_to_icon(61) == "10d"
    assert weather.code_to_icon(82) == "09d"
    assert weather.code_to_icon(73) == "13d"
    assert weather.code_to_icon(95) == "11d"


def test_code_to_icon_night_variant():
    assert weather.code_to_icon(0, is_day=0) == "01n"
    assert weather.code_to_icon(3, is_day=0) == "04n"


def test_code_to_icon_unknown_defaults_to_overcast():
    assert weather.code_to_icon(999) == "04d"


def _stub_response(status_code, payload):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = payload
    return resp


def test_get_current_success():
    requests.get.return_value = _stub_response(
        200, {"current_weather": {"weathercode": 3, "temperature": 14.2, "is_day": 1}}
    )
    wx = weather.get_current(51.5, -0.1)
    assert wx == {"weathercode": 3, "is_day": 1, "temperature": 14.2}
    requests.get.return_value.close.assert_called_once()


def test_get_current_defaults_is_day_when_missing():
    requests.get.return_value = _stub_response(200, {"current_weather": {"weathercode": 3}})
    wx = weather.get_current(51.5, -0.1)
    assert wx == {"weathercode": 3, "is_day": 1, "temperature": None}


def test_get_current_http_error_raises():
    requests.get.return_value = _stub_response(503, {})
    try:
        weather.get_current(51.5, -0.1)
        assert False, "expected RuntimeError"
    except RuntimeError as e:
        assert "503" in str(e)


def test_save_and_load_round_trip(tmp_path):
    path = str(tmp_path / "weather.json")
    weather.save_weather({"weathercode": 61}, path)
    assert weather.load_weather(path) == {"weathercode": 61}


def test_load_missing_returns_none(tmp_path):
    assert weather.load_weather(str(tmp_path / "nope.json")) is None
