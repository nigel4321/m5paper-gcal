from unittest.mock import MagicMock

import requests  # stubbed in conftest

from src import weather


def _stub_response(status_code, payload):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = payload
    return resp


def test_get_current_success():
    requests.get.return_value = _stub_response(200, {
        "daily": {"temperature_2m_max": [19.4], "temperature_2m_min": [11.8]}
    })
    wx = weather.get_current(51.5, -0.1)
    assert wx == {"temp_high": 19.4, "temp_low": 11.8}
    requests.get.return_value.close.assert_called_once()


def test_get_current_http_error_raises():
    requests.get.return_value = _stub_response(503, {})
    try:
        weather.get_current(51.5, -0.1)
        assert False, "expected RuntimeError"
    except RuntimeError as e:
        assert "503" in str(e)


def test_save_and_load_round_trip(tmp_path):
    path = str(tmp_path / "weather.json")
    weather.save_weather({"temp_high": 19.4, "temp_low": 11.8}, path)
    assert weather.load_weather(path) == {"temp_high": 19.4, "temp_low": 11.8}


def test_load_missing_returns_none(tmp_path):
    assert weather.load_weather(str(tmp_path / "nope.json")) is None
