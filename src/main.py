import M5
from M5 import *

import display
from mock_data import MOCK_EVENTS

# Phase 2: static values. Real battery/time wired in Phase 4.
MOCK_BATTERY_PCT = 84
MOCK_LAST_UPDATED = "09:15"


def setup():
    M5.begin()
    print("m5paper-gcal: rendering mock events")
    display.render_all(MOCK_EVENTS, MOCK_BATTERY_PCT, MOCK_LAST_UPDATED)


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
