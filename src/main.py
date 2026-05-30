import M5
from M5 import *

import calendar
import config
import display
from mock_data import MOCK_EVENTS

# Phase 2: static values. Real battery/time wired in Phase 4.
MOCK_BATTERY_PCT = 84
MOCK_LAST_UPDATED = "09:15"


def fetch_events():
    """Fetch live events. WiFi connection is added in Phase 4; until then
    (or on any failure) we fall back to mock data so the device still renders."""
    token = calendar.refresh_access_token(
        config.CLIENT_ID, config.CLIENT_SECRET, config.REFRESH_TOKEN
    )
    return calendar.get_upcoming_events(token, config.MAX_EVENTS)


def setup():
    M5.begin()
    try:
        events = fetch_events()
        print("m5paper-gcal: rendering live events")
    except Exception as e:
        events = MOCK_EVENTS
        print("m5paper-gcal: fetch failed ({}), rendering mock events".format(e))
    display.render_all(events, MOCK_BATTERY_PCT, MOCK_LAST_UPDATED)


def loop():
    M5.update()


if __name__ == "__main__":
    try:
        setup()
        while True:
            loop()
    except (Exception, KeyboardInterrupt) as e:
        try:
            from utility import print_error_msg
            print_error_msg(e)
        except ImportError:
            print("please update all packages")
