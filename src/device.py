import time

import network

import M5


def connect_wifi(ssid, password, timeout_s=20):
    """Connect to WiFi. Returns True on success, False on timeout."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        return True
    try:
        wlan.disconnect()
    except OSError:
        pass
    time.sleep(0.1)
    wlan.connect(ssid, password)
    deadline = time.time() + timeout_s
    while not wlan.isconnected():
        if time.time() > deadline:
            return False
        time.sleep(0.5)
    return True


def disconnect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.disconnect()
    wlan.active(False)


def sync_time():
    """Set the RTC from NTP (UTC). Requires an active connection."""
    import ntptime
    ntptime.settime()


def battery_percent():
    try:
        return int(M5.Power.getBatteryLevel())
    except Exception:
        return 0


def minutes_to_seconds(minutes):
    return minutes * 60


def deep_sleep(minutes):
    """Enter deep sleep; the device reboots and re-runs main.py on wake.

    Uses M5.Power.timerSleep, which routes the wake through the M5Paper's
    BM8563 RTC and properly cycles the main power rail. machine.deepsleep
    does not coordinate with the power IC and leaves the device asleep.
    """
    M5.Power.timerSleep(minutes_to_seconds(minutes))
