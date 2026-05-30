# M5Paper Google Calendar Display — Build Plan

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Language | MicroPython (UIFlow 2.0) | Platform constraint; UIFlow 2.0 runs MicroPython |
| Google Calendar auth | Direct OAuth on device | No backend dependency; refresh token stored on device |
| Battery strategy | Deep sleep + RTC wake | E-ink retains image without power; wake every N minutes to refresh |
| Build order | UI with mock data first | Validate display layout on real hardware before adding auth complexity |

---

## Phase 1 — Project Setup

**Goal:** Working local dev environment; code can be pushed to device and validated in CI.

### Steps
1. Define repo structure (see below)
2. Add `requirements.txt` / tooling notes for UIFlow 2.0 upload workflow
3. Add GitHub Actions workflow: lint MicroPython with `ruff` or `pylint` (micropython stubs)
4. Write a minimal `main.py` that prints "hello" to the serial console and confirm it runs on device

### Verify
- `main.py` runs on M5Paper via UIFlow 2.0 upload
- GitHub Actions passes on push

### Repo structure
```
m5paper-gcal/
├── src/
│   ├── main.py          # Entry point
│   ├── display.py       # All rendering logic
│   ├── calendar.py      # Google Calendar API + OAuth
│   ├── config.py        # WiFi creds, token storage, settings
│   └── mock_data.py     # Static event fixtures for Phase 2
├── tests/               # Host-side unit tests (pure Python, no device needed)
├── .github/workflows/
│   └── ci.yml
├── PLAN.md
└── PROJECT.md
```

---

## Phase 2 — UI with Mock Data

**Goal:** A complete, visually correct e-ink display layout driven by static mock data. Runs on the real device. No network calls.

### M5Paper display specs
- Screen: 4.7" e-ink, 960×540 px, greyscale
- UIFlow 2.0 display APIs: `M5.Lcd` or `epaper` module

### Layout design
Events span across days — each event row shows its date when it differs from the previous row.

```
┌─────────────────────────────────────────────┐
│  Next 5 events                       🔋 84% │
├─────────────────────────────────────────────┤
│  Friday 30 May                              │
│  09:00  Team standup                        │
│         Google Meet · 30 min               │
│                                             │
│  11:00  Design review                       │
│         Conference Room B · 1 hr           │
│                                             │
│  Saturday 31 May                            │
│  10:00  1:1 with Alice                      │
│         Zoom · 45 min                       │
├─────────────────────────────────────────────┤
│  Updated 09:15                              │
└─────────────────────────────────────────────┘
```

### Mock data (`src/mock_data.py`)
- 5 hardcoded events spanning at least 2 different days
- Covers edge cases: all-day event, event with no location, back-to-back events on the same day, event on a following day

### Steps
1. Implement `mock_data.py` with fixture events
2. Implement `display.py`:
   - `render_header(date_str, battery_pct)` — date + battery
   - `render_event(event)` — single event row
   - `render_footer(last_updated_str)` — last refresh timestamp
   - `render_all(events)` — full screen refresh
3. Wire into `main.py` to call `render_all(MOCK_EVENTS)` on boot
4. Upload to device and visually inspect

### Verify
- All mock events display correctly on device
- Layout looks correct at 960×540
- No rendering artefacts on e-ink (ghosting, clipping)
- Edge cases render without crashing (empty day, long event title)

---

## Phase 3 — Google Calendar OAuth (Direct on Device)

**Goal:** Device can fetch real events from Google Calendar using a stored OAuth refresh token.

### Auth flow
Google's [OAuth 2.0 for TV/limited-input devices](https://developers.google.com/identity/protocols/oauth2/limited-input-device) — user authorises once on a desktop, device gets a refresh token that is stored in a config file.

### One-time setup (done by developer, not on device)
1. Create a Google Cloud project, enable Calendar API
2. Create OAuth credentials for "TV and limited-input devices"
3. Run the included `tools/get_token.py` script on desktop to complete OAuth flow
4. Copy the resulting `refresh_token` into `src/config.py` on the device

### On-device token refresh (every wake cycle)
```
POST https://oauth2.googleapis.com/token
  grant_type=refresh_token
  client_id=...
  client_secret=...
  refresh_token=...
→ access_token (valid 1 hr)
```

### Calendar fetch
Fetch the next 5 upcoming events from now, regardless of which day they fall on.

```
GET https://www.googleapis.com/calendar/v3/calendars/primary/events
  ?timeMin=<now UTC>
  &maxResults=5
  &singleEvents=true
  &orderBy=startTime
  Authorization: Bearer <access_token>
```

### Steps
1. Implement `calendar.py`:
   - `refresh_access_token()` — POST to token endpoint, return access token
   - `get_upcoming_events(access_token)` — GET next 5 events from now, return list of dicts
2. Implement `tools/get_token.py` (runs on desktop, not device)
3. Add `config.py` fields: `CLIENT_ID`, `CLIENT_SECRET`, `REFRESH_TOKEN`
4. Update `main.py` to call real calendar instead of mock data
5. Add `tests/test_calendar.py` with host-side unit tests (mock HTTP responses)

### Verify
- `refresh_access_token()` returns a valid token
- `get_todays_events()` returns correctly shaped event dicts
- Unit tests pass in CI
- Real events display on device

---

## Phase 4 — WiFi + Deep Sleep

**Goal:** Device connects to WiFi only when needed, fetches events, updates display, then deep sleeps. Battery life measured.

### Wake cycle
```
Boot → Connect WiFi → Refresh token → Fetch events → Render display → Disconnect WiFi → Deep sleep N min
```

### Steps
1. Implement WiFi connect/disconnect in `config.py`
2. Wrap main loop in try/except: on failure, render an error state on display before sleeping
3. Implement deep sleep via `machine.deepsleep(ms)` — configurable interval (default 30 min)
4. Add battery % read to pass into `render_header()`
5. Tune sleep interval based on real battery measurements

### Error states to handle
- WiFi connect failure → "No WiFi" on display
- Token refresh failure → "Auth error" on display  
- Calendar API failure → show stale data with "⚠ update failed" indicator

### Verify
- Full wake → fetch → render → sleep cycle completes in < 30 seconds
- Device wakes on schedule (confirm with serial output on first few cycles)
- Error states render correctly when WiFi is disabled
- Battery % shown accurately

---

## Phase 5 — Integration & Polish

**Goal:** Production-ready. Handles all edge cases gracefully. Display is clean and readable.

### Steps
1. Review display layout with real data (event titles may be longer than mock data)
2. Add text truncation for long titles/locations
3. Handle multi-day events correctly
4. Handle timezone offset (device RTC vs Google Calendar UTC timestamps)
5. Final battery life measurement over 24 hours

### Verify
- 24-hour run without crash
- Battery life acceptable for use case
- All GitHub Actions green

---

## CI Setup

```yaml
# .github/workflows/ci.yml
on: [push, pull_request]
jobs:
  lint:
    - ruff check src/
  test:
    - pytest tests/
```

Tests run on host Python (not device). Device-specific APIs (`machine`, `network`, `M5`) are mocked in `tests/conftest.py`.

---

## Open Questions

- What refresh interval is acceptable? (battery vs freshness trade-off)
- Should multi-day / all-day events be shown differently?
- Single calendar or multiple? (can add later)
