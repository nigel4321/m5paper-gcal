import json
import time

try:
    import requests
except ImportError:
    import urequests as requests

TOKEN_URL = "https://oauth2.googleapis.com/token"
EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
CACHE_PATH = "events.json"


# --- Pure helpers (no network; unit tested on host) ---

def _format_rfc3339(t):
    """time tuple (year, month, mday, hour, min, sec, ...) -> 'YYYY-MM-DDTHH:MM:SSZ'."""
    return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}Z".format(t[0], t[1], t[2], t[3], t[4], t[5])


def _now_rfc3339():
    return _format_rfc3339(time.gmtime())


def _quote(value):
    """Minimal percent-encoding for query values (enough for an RFC3339 timestamp)."""
    return value.replace(":", "%3A").replace("+", "%2B")


def _normalise_event(item):
    """Google Calendar API event -> the dict shape display.py expects."""
    start_obj = item.get("start", {})
    end_obj = item.get("end", {})
    all_day = "date" in start_obj
    return {
        "title": item.get("summary", "(no title)"),
        "location": item.get("location", ""),
        "all_day": all_day,
        "start": start_obj.get("date") if all_day else start_obj.get("dateTime", ""),
        "end": end_obj.get("date") if all_day else end_obj.get("dateTime", ""),
    }


def parse_events(data):
    """Parse a Calendar API 'events list' response body into our event dicts."""
    return [_normalise_event(item) for item in data.get("items", [])]


# --- Cache (last-good events survive deep sleep on flash) ---

def save_events(events, path=CACHE_PATH):
    with open(path, "w") as f:
        json.dump(events, f)


def load_events(path=CACHE_PATH):
    """Return cached events, or None if nothing has been cached yet."""
    try:
        with open(path) as f:
            return json.load(f)
    except OSError:
        return None


# --- Network (MicroPython requests / urequests) ---

def refresh_access_token(client_id, client_secret, refresh_token):
    """Exchange the stored refresh token for a short-lived access token."""
    body = (
        "grant_type=refresh_token"
        "&client_id={}&client_secret={}&refresh_token={}".format(
            client_id, client_secret, refresh_token
        )
    )
    resp = requests.post(
        TOKEN_URL,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        if resp.status_code != 200:
            raise RuntimeError("token refresh failed: HTTP {}".format(resp.status_code))
        return resp.json()["access_token"]
    finally:
        resp.close()


def get_upcoming_events(access_token, max_results=5, time_min=None):
    """Fetch the next `max_results` events from now, regardless of day."""
    if time_min is None:
        time_min = _now_rfc3339()
    url = (
        "{}?maxResults={}&singleEvents=true&orderBy=startTime&timeMin={}".format(
            EVENTS_URL, max_results, _quote(time_min)
        )
    )
    resp = requests.get(url, headers={"Authorization": "Bearer " + access_token})
    try:
        if resp.status_code != 200:
            raise RuntimeError("events fetch failed: HTTP {}".format(resp.status_code))
        return parse_events(resp.json())
    finally:
        resp.close()
