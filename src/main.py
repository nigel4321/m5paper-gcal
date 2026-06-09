import time

import M5

import calendar
import config
import device
import display
import weather


def run_cycle():
    """One wake cycle: connect, fetch, render, disconnect. Returns True if WiFi connected."""
    events = None
    wx = None
    error = None
    wifi_ok = False

    if not device.connect_wifi(config.WIFI_SSID, config.WIFI_PASSWORD):
        error = ("No WiFi", "Could not connect to {}".format(config.WIFI_SSID))
    else:
        wifi_ok = True
        try:
            device.sync_time()
        except Exception as e:
            print("time sync failed:", e)  # non-fatal; RTC may already be set
        try:
            token = calendar.refresh_access_token(
                config.CLIENT_ID, config.CLIENT_SECRET, config.REFRESH_TOKEN
            )
        except Exception as e:
            print("auth failed:", e)
            error = ("Auth error", "Token refresh failed")
        else:
            try:
                events = calendar.get_upcoming_events(token, config.MAX_EVENTS)
                calendar.save_events(events)
            except Exception as e:
                print("fetch failed:", e)  # fall through to stale cache below
        try:
            wx = weather.get_current(config.WEATHER_LAT, config.WEATHER_LNG)
            weather.save_weather(wx)
        except Exception as e:
            print("weather fetch failed:", e)
            wx = weather.load_weather()
        device.disconnect_wifi()

    if wx is None:
        wx = weather.load_weather()
    temp_high = wx.get("temp_high") if wx else None
    temp_low = wx.get("temp_low") if wx else None

    battery = device.battery_percent()
    local_now = display.to_london(time.gmtime())
    updated = display.format_clock(local_now)
    today = display.date_str_from_time(local_now)

    if events is not None:
        display.render_all(events, battery, updated, today=today, temp_high=temp_high, temp_low=temp_low)
    elif error:
        display.render_error(error[0], error[1], battery)
    else:
        cached = calendar.load_events()
        if cached:
            display.render_all(
                cached, battery, updated, today=today,
                temp_high=temp_high, temp_low=temp_low, warning="update failed"
            )
        else:
            display.render_error("Update failed", "Could not reach Google Calendar", battery)

    return wifi_ok


def main():
    M5.begin()
    wifi_ok = False
    try:
        wifi_ok = run_cycle()
    except Exception as e:
        try:
            from utility import print_error_msg
            print_error_msg(e)
        except ImportError:
            print(e)
    finally:
        # Retry sooner when offline; use configured interval once connected.
        wifi_fail_interval = getattr(config, "SLEEP_INTERVAL_WIFI_FAIL_MIN", 60)
        sleep_min = config.SLEEP_INTERVAL_MIN if wifi_ok else wifi_fail_interval
        device.deep_sleep(sleep_min)


if __name__ == "__main__":
    main()
