import M5

# M5Paper landscape resolution (after setRotation(1))
WIDTH = 960
HEIGHT = 540

# Greyscale colours (M5GFX RGB565-style hex; e-ink renders as grey levels)
BLACK = 0x000000
WHITE = 0xFFFFFF
GREY = 0x888888

# Layout
MARGIN = 24
HEADER_H = 64
FOOTER_H = 44
TITLE_MAX_CHARS = 34
DETAIL_MAX_CHARS = 40

_WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
_MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


# --- Pure helpers (no device dependency; unit tested on host) ---

def _date_ordinal(y, m, d):
    """Julian Day Number — used only for date/time differences."""
    a = (14 - m) // 12
    yy = y + 4800 - a
    mm = m + 12 * a - 3
    return d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - yy // 100 + yy // 400 - 32045


def day_of_week(y, m, d):
    """0=Sunday .. 6=Saturday (Sakamoto's algorithm)."""
    t = [0, 3, 2, 5, 0, 3, 5, 1, 4, 6, 2, 4]
    if m < 3:
        y -= 1
    return (y + y // 4 - y // 100 + y // 400 + t[m - 1] + d) % 7


def event_date(event):
    """Date portion 'YYYY-MM-DD' of an event's start."""
    return event["start"][:10]


def format_date_heading(date_str):
    """'2026-05-30' -> 'Saturday 30 May'."""
    y, m, d = int(date_str[:4]), int(date_str[5:7]), int(date_str[8:10])
    return "{} {} {}".format(_WEEKDAYS[day_of_week(y, m, d)], d, _MONTHS[m - 1])


def format_time(start):
    """'2026-05-30T09:00:00' -> '09:00'."""
    return start[11:16]


def format_duration(start, end):
    """Minutes between two ISO datetimes, formatted as '30 min' / '1 hr' / '1 hr 30 min'."""
    sy, sm, sd = int(start[:4]), int(start[5:7]), int(start[8:10])
    ey, em, ed = int(end[:4]), int(end[5:7]), int(end[8:10])
    start_min = _date_ordinal(sy, sm, sd) * 1440 + int(start[11:13]) * 60 + int(start[14:16])
    end_min = _date_ordinal(ey, em, ed) * 1440 + int(end[11:13]) * 60 + int(end[14:16])
    total = end_min - start_min
    if total <= 0:
        return ""
    hrs, mins = total // 60, total % 60
    if hrs == 0:
        return "{} min".format(mins)
    if mins == 0:
        return "{} hr".format(hrs)
    return "{} hr {} min".format(hrs, mins)


def truncate(text, max_chars):
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1] + "…"


def format_detail_line(event):
    """Secondary line: 'location · duration', or whichever part is present."""
    if event.get("all_day"):
        return ""
    duration = format_duration(event["start"], event["end"])
    location = event.get("location", "")
    if location and duration:
        line = "{} · {}".format(location, duration)
    else:
        line = location or duration
    return truncate(line, DETAIL_MAX_CHARS)


def group_events_by_day(events):
    """[(date_str, [event, ...]), ...] preserving input order."""
    groups = []
    for event in events:
        date_str = event_date(event)
        if groups and groups[-1][0] == date_str:
            groups[-1][1].append(event)
        else:
            groups.append((date_str, [event]))
    return groups


# --- Device rendering (M5Paper / UIFlow 2.0) ---

def _draw_battery(x, y, pct):
    """Battery glyph with proportional fill, right-aligned ending at x."""
    body_w, body_h = 48, 24
    bx = x - body_w
    M5.Lcd.drawRect(bx, y, body_w, body_h, BLACK)
    M5.Lcd.fillRect(x, y + 7, 4, 10, BLACK)  # terminal nub
    fill_w = int((body_w - 4) * max(0, min(100, pct)) / 100)
    if fill_w > 0:
        M5.Lcd.fillRect(bx + 2, y + 2, fill_w, body_h - 4, BLACK)
    M5.Lcd.setTextSize(2)
    M5.Lcd.setTextColor(BLACK)
    M5.Lcd.drawString("{}%".format(pct), bx - 56, y + 2)


def render_header(title, battery_pct):
    M5.Lcd.setTextSize(3)
    M5.Lcd.setTextColor(BLACK)
    M5.Lcd.drawString(title, MARGIN, 18)
    _draw_battery(WIDTH - MARGIN, 18, battery_pct)
    M5.Lcd.drawFastHLine(MARGIN, HEADER_H, WIDTH - 2 * MARGIN, BLACK)


def render_day_heading(date_str, y):
    M5.Lcd.setTextSize(2)
    M5.Lcd.setTextColor(GREY)
    M5.Lcd.drawString(format_date_heading(date_str), MARGIN, y)
    return y + 30


def render_event(event, y):
    M5.Lcd.setTextColor(BLACK)
    time_label = "All day" if event.get("all_day") else format_time(event["start"])
    M5.Lcd.setTextSize(3)
    M5.Lcd.drawString(time_label, MARGIN, y)
    M5.Lcd.drawString(truncate(event["title"], TITLE_MAX_CHARS), MARGIN + 130, y)
    detail = format_detail_line(event)
    if detail:
        M5.Lcd.setTextSize(2)
        M5.Lcd.setTextColor(GREY)
        M5.Lcd.drawString(detail, MARGIN + 130, y + 30)
        return y + 64
    return y + 44


def format_clock(t):
    """time tuple -> 'HH:MM'."""
    return "{:02d}:{:02d}".format(t[3], t[4])


def render_footer(last_updated, warning=None):
    y = HEIGHT - FOOTER_H
    M5.Lcd.drawFastHLine(MARGIN, y, WIDTH - 2 * MARGIN, BLACK)
    M5.Lcd.setTextSize(2)
    M5.Lcd.setTextColor(GREY)
    M5.Lcd.drawString("Updated {}".format(last_updated), MARGIN, y + 12)
    if warning:
        M5.Lcd.setTextColor(BLACK)
        M5.Lcd.drawString("! " + warning, WIDTH - MARGIN - 240, y + 12)


def render_all(events, battery_pct, last_updated, warning=None):
    """Full-screen refresh: header, day-grouped events, footer."""
    M5.Lcd.setRotation(1)
    M5.Lcd.fillScreen(WHITE)
    render_header("Next 5 events", battery_pct)
    y = HEADER_H + 20
    for date_str, day_events in group_events_by_day(events):
        y = render_day_heading(date_str, y)
        for event in day_events:
            y = render_event(event, y)
        y += 8
    render_footer(last_updated, warning)


def render_error(title, detail, battery_pct):
    """Full-screen error state (no WiFi / auth failure / unreachable API)."""
    M5.Lcd.setRotation(1)
    M5.Lcd.fillScreen(WHITE)
    render_header("Next 5 events", battery_pct)
    M5.Lcd.setTextColor(BLACK)
    M5.Lcd.setTextSize(5)
    M5.Lcd.drawString(title, MARGIN, 210)
    M5.Lcd.setTextSize(2)
    M5.Lcd.setTextColor(GREY)
    M5.Lcd.drawString(detail, MARGIN, 290)
