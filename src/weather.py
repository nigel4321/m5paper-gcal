import json

try:
    import requests
except ImportError:
    import urequests as requests

API_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude={}&longitude={}"
    "&daily=temperature_2m_max,temperature_2m_min"
    "&timezone=Europe%2FLondon&forecast_days=1"
)
CACHE_PATH = "weather.json"


def get_current(lat, lng):
    """Fetch today's forecast high/low from Open-Meteo."""
    resp = requests.get(API_URL.format(lat, lng))
    try:
        if resp.status_code != 200:
            raise RuntimeError("weather fetch failed: HTTP {}".format(resp.status_code))
        daily = resp.json()["daily"]
        return {
            "temp_high": daily["temperature_2m_max"][0],
            "temp_low": daily["temperature_2m_min"][0],
        }
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
