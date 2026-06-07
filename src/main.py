import time

import M5

import calendar
import config
import device
import display
import weather


def run_cycle():
    """One wake cycle: connect, fetch, render, disconnect."""
    events = None
    wx = None
    error = None

    if not device.connect_wifi(config.WIFI_SSID, config.WIFI_PASSWORD):
        error = ("No WiFi", "Could not connect to {}".format(config.WIFI_SSID))
    else:
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
        if wx:
            try:
                weather.ensure_icon(weather.code_to_icon(wx["weathercode"], wx.get("is_day", 1)))
            except Exception as e:
                print("icon fetch failed:", e)
        device.disconnect_wifi()

    if wx is None:
        wx = weather.load_weather()
    icon = weather.code_to_icon(wx["weathercode"], wx.get("is_day", 1)) if wx else None
    temperature = wx.get("temperature") if wx else None

    battery = device.battery_percent()
    local_now = display.to_london(time.gmtime())
    updated = display.format_clock(local_now)
    today = display.date_str_from_time(local_now)

    if events is not None:
        display.render_all(events, battery, updated, today=today, weather_icon=icon, temperature=temperature)
    elif error:
        display.render_error(error[0], error[1], battery)
    else:
        cached = calendar.load_events()
        if cached:
            display.render_all(
                cached, battery, updated, today=today, weather_icon=icon, temperature=temperature, warning="update failed"
            )
        else:
            display.render_error("Update failed", "Could not reach Google Calendar", battery)


def main():
    M5.begin()
    try:
        run_cycle()
    except Exception as e:
        try:
            from utility import print_error_msg
            print_error_msg(e)
        except ImportError:
            print(e)
    finally:
        # Always sleep, even after an unexpected error, to preserve battery.
        device.deep_sleep(config.SLEEP_INTERVAL_MIN)


if __name__ == "__main__":
    main()
