# m5paper-gcal

Display your upcoming Google Calendar events plus current weather on an
[M5Paper](https://docs.m5stack.com/en/core/m5paper) e-ink device.

The device wakes on a timer, connects to WiFi, fetches upcoming events
directly from the Google Calendar API (OAuth on-device, no backend) and the
current weather from Open-Meteo (no API key), renders to the e-ink screen,
then deep sleeps to conserve battery.

The display shows today's date with a weather icon at the top, then events
grouped by day, with the last-updated time and battery in the footer. Times
are shown in London time (BST/GMT) and switch automatically each year.

## How it works

```
Boot → Connect WiFi → NTP → Refresh OAuth → Fetch events → Fetch weather
     → Render display → Disconnect WiFi → Deep sleep N minutes → (repeat)
```

The e-ink display retains its image with no power, so the screen stays
readable the whole time the device is asleep.

## Project layout

| File | Role |
|---|---|
| `src/main.py` | Entry point — runs one wake cycle then deep sleeps |
| `src/display.py` | Layout/rendering, BST/GMT conversion, date helpers |
| `src/calendar.py` | Google Calendar OAuth, event fetch, on-flash event cache |
| `src/weather.py` | Open-Meteo client, WMO→OWM icon mapping, icon download + cache |
| `src/device.py` | WiFi, NTP time sync, battery read, deep sleep (via `M5.Power.timerSleep`) |
| `src/config.example.py` | Template for `config.py` (WiFi/OAuth/weather settings) |
| `src/mock_data.py` | Sample events used for tests / offline display checks |
| `tools/get_token.py` | One-time desktop helper to obtain a refresh token |
| `tools/preview.py` | Render the layout to a PNG on the host (mock or live data) |

## Getting your Google Calendar credentials

### A. Create the project & enable the API
1. Go to <https://console.cloud.google.com> and sign in.
2. Top bar → project dropdown → **New Project** (e.g. "m5paper-gcal") →
   **Create**, then select it.
3. **APIs & Services → Library** → search **"Google Calendar API"** → **Enable**.

### B. Configure the OAuth consent screen
4. **APIs & Services → OAuth consent screen** → User Type **External** → **Create**.
5. Fill in App name, your email for support + developer contact →
   **Save and Continue**.
6. **Scopes** → **Add or remove scopes** → add
   `https://www.googleapis.com/auth/calendar.readonly` → **Update** →
   **Save and Continue**.
7. **Test users** → **Add users** → add your Google account → **Save**.
   (Keeping the app in "Testing" mode is fine — refresh tokens stay valid as
   long as you remain a listed test user.)

### C. Create the OAuth client
8. **APIs & Services → Credentials → Create Credentials → OAuth client ID**.
9. Application type → **TVs and Limited Input devices** → **Create**.
10. Copy the **Client ID** and **Client Secret**.

### D. Get your refresh token
11. From the repo root, run:
    ```
    CLIENT_ID=<your-id> CLIENT_SECRET=<your-secret> python3 tools/get_token.py
    ```
12. The script prints a URL and a code — visit the URL, enter the code, and
    approve access (click through the "unverified app" warning, since the app
    is in Testing mode).
13. It then prints a `REFRESH_TOKEN = "..."` line.

### E. Configure the device
14. Copy the template and fill in your values:
    ```
    cp src/config.example.py src/config.py
    ```
    Edit `src/config.py` and set:
    - `WIFI_SSID` / `WIFI_PASSWORD`
    - `CLIENT_ID`, `CLIENT_SECRET`, `REFRESH_TOKEN`
    - `WEATHER_LAT` / `WEATHER_LNG` — the location used for the weather icon
      (defaults to London). Open-Meteo is keyless.
    - `SLEEP_INTERVAL_MIN` — how often the device wakes (in minutes)
    - `MAX_EVENTS` — how many upcoming events to show

    `config.py` is gitignored, so your secrets are never committed.

## Uploading to the device

Using the [UIFlow 2.0](https://docs.m5stack.com/en/uiflow/uiflow2/intro)
editor, upload the files to these locations on the device:

| Host file | Device path |
|---|---|
| `src/main.py` | `/flash/main.py` |
| `src/display.py` | `/flash/libs/display.py` |
| `src/calendar.py` | `/flash/libs/calendar.py` |
| `src/weather.py` | `/flash/libs/weather.py` |
| `src/device.py` | `/flash/libs/device.py` |
| `src/config.py` | `/flash/libs/config.py` |

`/flash/libs/` is on `sys.path` by default, so the modules import without
any path prefix. `main.py` must live at the device **root** for the
autoboot flow below to pick it up.

Weather icons are downloaded on demand from `openweathermap.org/img/wn/`
and cached at `/flash/icons/` — no manual upload needed. The first wake
needs network for both the calendar fetch and the initial icon download;
after that, only icons for new weather conditions are fetched.

## Autoboot

So the device runs the calendar on power-on and after every deep-sleep
wake, switch UIFlow's `boot.py` out of "show startup menu" mode and into
"run `main.py` directly" mode. Do this **once** at the REPL:

```python
import esp32
nvs = esp32.NVS("uiflow")
nvs.set_u8("boot_option", 0)
nvs.commit()
```

Then hard-reboot. You should see the `print(...)` output from `main.py`
on the serial console, the display refresh, then deep sleep until the
next wake.

To get back to the UIFlow startup menu (e.g. to reconnect to the cloud
editor), hold **BtnA** and press reset.

**Heads-up:** hitting **DOWNLOAD** in the UIFlow cloud editor resets
`boot_option` to `2` (network setup only, won't run `main.py`). Upload
files via the UIFlow file manager instead, or re-run the NVS snippet
above after a DOWNLOAD.

## Previewing the display on your laptop

`tools/preview.py` renders the same layout to a PNG (540×960, portrait —
identical to the device's e-ink panel) so you can iterate on the design
without touching hardware.

```
.venv/bin/python tools/preview.py                # MOCK_EVENTS + no icon
.venv/bin/python tools/preview.py --open         # also open the PNG
.venv/bin/python tools/preview.py --live         # real events + real weather
.venv/bin/python tools/preview.py --weather rain # force a specific icon
.venv/bin/python tools/preview.py --events events.json  # events from a JSON file
```

`--live` reuses `src/config.py` to refresh the OAuth token, pulls your
upcoming events from Google Calendar, and fetches the current weather from
Open-Meteo for `WEATHER_LAT` / `WEATHER_LNG`. Icons are downloaded to a
local `.icon_cache/` (gitignored) on first use.

Fonts fall back through Montserrat → Helvetica → Arial → DejaVu, so the
preview is visually close to but not pixel-identical to the device's
Montserrat rendering.

## Development

Tests run on host Python with the device modules stubbed — no hardware needed.

```
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/ruff check src/
.venv/bin/pytest
```

CI runs the same lint and tests on every push and pull request.

See [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) for the open display-rendering
quirk and the hypotheses we've already ruled out.
