import json
import os

try:
    import requests
except ImportError:
    import urequests as requests

API_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude={}&longitude={}&current_weather=true"
)
ICON_URL = "http://openweathermap.org/img/wn/{}@2x.png"
CACHE_PATH = "weather.json"
ICON_DIR = "/flash/icons"

# WMO weathercode -> OpenWeatherMap icon prefix (day/night suffix added at lookup).
# OWM icon codes: 01=clear, 02=few clouds, 03=scattered, 04=broken/overcast,
#                 09=shower rain, 10=rain, 11=thunder, 13=snow, 50=mist
_WMO_TO_OWM = {
    0: "01",
    1: "02", 2: "03",
    3: "04",
    45: "50", 48: "50",
    51: "09", 53: "09", 55: "09",
    56: "09", 57: "09",
    61: "10", 63: "10", 65: "10",
    66: "13", 67: "13",
    71: "13", 73: "13", 75: "13", 77: "13",
    80: "09", 81: "09", 82: "09",
    85: "13", 86: "13",
    95: "11", 96: "11", 99: "11",
}


def code_to_icon(weathercode, is_day=1):
    """WMO weathercode + day/night flag -> OWM icon name (e.g. '01d', '10n')."""
    prefix = _WMO_TO_OWM.get(weathercode, "04")
    return prefix + ("d" if is_day else "n")


def get_current(lat, lng):
    """Fetch current weather from Open-Meteo. Returns weathercode + is_day."""
    resp = requests.get(API_URL.format(lat, lng))
    try:
        if resp.status_code != 200:
            raise RuntimeError("weather fetch failed: HTTP {}".format(resp.status_code))
        cw = resp.json()["current_weather"]
        return {"weathercode": cw["weathercode"], "is_day": cw.get("is_day", 1)}
    finally:
        resp.close()


def ensure_icon(code, cache_dir=ICON_DIR):
    """Return the path to the OWM icon for `code`, downloading if not cached."""
    path = "{}/{}.png".format(cache_dir, code)
    try:
        with open(path, "rb"):
            return path
    except OSError:
        pass
    try:
        os.mkdir(cache_dir)
    except OSError:
        pass
    resp = requests.get(ICON_URL.format(code))
    try:
        if resp.status_code != 200:
            raise RuntimeError("icon fetch failed: HTTP {}".format(resp.status_code))
        with open(path, "wb") as f:
            f.write(resp.content)
        return path
    finally:
        resp.close()


def save_weather(weather, path=CACHE_PATH):
    with open(path, "w") as f:
        json.dump(weather, f)


def load_weather(path=CACHE_PATH):
    try:
        with open(path) as f:
            return json.load(f)
    except OSError:
        return None
