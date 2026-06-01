# m5paper-gcal

Display the next 5 events from a Google Calendar on an
[M5Paper](https://docs.m5stack.com/en/core/m5paper) e-ink device.

The device wakes on a timer, connects to WiFi, fetches your upcoming events
directly from the Google Calendar API (OAuth on-device, no backend), renders
them to the e-ink screen, then deep sleeps to conserve battery.

## How it works

```
Boot → Connect WiFi → Sync time (NTP) → Refresh token → Fetch events
     → Render display → Disconnect WiFi → Deep sleep N minutes → (repeat)
```

The e-ink display retains its image with no power, so the screen stays
readable the whole time the device is asleep.

## Project layout

| File | Role |
|---|---|
| `src/main.py` | Entry point — runs one wake cycle then deep sleeps |
| `src/display.py` | Layout and rendering (header, events, footer, error states) |
| `src/calendar.py` | Google Calendar OAuth, event fetch, and on-flash cache |
| `src/device.py` | WiFi, NTP time sync, battery read, deep sleep |
| `src/config.example.py` | Template for `config.py` (WiFi/OAuth credentials, settings) |
| `src/mock_data.py` | Sample events used for tests / offline display checks |
| `tools/get_token.py` | One-time desktop helper to obtain a refresh token |

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
    Edit `src/config.py` and set `CLIENT_ID`, `CLIENT_SECRET`, `REFRESH_TOKEN`,
    plus `WIFI_SSID` / `WIFI_PASSWORD`. `config.py` is gitignored, so your
    secrets are never committed.

## Uploading to the device

Using the [UIFlow 2.0](https://docs.m5stack.com/en/uiflow/uiflow2/intro)
editor, upload the files to these locations on the device:

| Host file | Device path |
|---|---|
| `src/main.py` | `/flash/main.py` |
| `src/display.py` | `/flash/libs/display.py` |
| `src/calendar.py` | `/flash/libs/calendar.py` |
| `src/device.py` | `/flash/libs/device.py` |
| `src/config.py` | `/flash/libs/config.py` |

`/flash/libs/` is on `sys.path` by default, so the modules import without
any path prefix. `main.py` must live at the device **root** for the
autoboot flow below to pick it up.

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

## Development

Tests run on host Python with the device modules stubbed — no hardware needed.

```
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/ruff check src/
.venv/bin/pytest
```

CI runs the same lint and tests on every push and pull request.
