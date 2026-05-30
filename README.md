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
| `src/config.py` | WiFi credentials, OAuth credentials, settings |
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
14. Edit `src/config.py` and fill in `CLIENT_ID`, `CLIENT_SECRET`,
    `REFRESH_TOKEN`, plus `WIFI_SSID` / `WIFI_PASSWORD`.

## Uploading to the device

The device uses a flat filesystem, so all source files live in the device
**root** (do not recreate the `src/` folder on the device). Using the
[UIFlow 2.0](https://docs.m5stack.com/en/uiflow/uiflow2/intro) editor, upload:

- `main.py`
- `display.py`
- `calendar.py`
- `device.py`
- `config.py`

Then run `main.py`.

## Development

Tests run on host Python with the device modules stubbed — no hardware needed.

```
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/ruff check src/
.venv/bin/pytest
```

CI runs the same lint and tests on every push and pull request.
