import M5

# M5Paper portrait resolution (after setRotation(0))
WIDTH = 540
HEIGHT = 960

# Greyscale colours (M5GFX RGB565-style hex; e-ink renders as grey levels)
BLACK = 0x000000
WHITE = 0xFFFFFF
GREY = 0x888888

# Layout
MARGIN = 24
FOOTER_H = 44
TIME_COL_W = 110
TITLE_MAX_CHARS = 28
DETAIL_MAX_CHARS = 42

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


def truncate(text, max_chars):
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1] + "…"


def format_detail_line(event):
    """Secondary line: location only (empty if all-day or no location)."""
    if event.get("all_day"):
        return ""
    return truncate(event.get("location", ""), DETAIL_MAX_CHARS)


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

def _use(font, color=BLACK):
    M5.Lcd.setFont(font)
    M5.Lcd.setTextSize(1)
    M5.Lcd.setTextColor(color, WHITE)


def _draw_battery(x, y, pct):
    """Battery glyph with proportional fill, right-aligned ending at x."""
    body_w, body_h = 44, 22
    bx = x - body_w
    M5.Lcd.drawRect(bx, y, body_w, body_h, BLACK)
    M5.Lcd.fillRect(x, y + 6, 4, 10, BLACK)  # terminal nub
    fill_w = int((body_w - 4) * max(0, min(100, pct)) / 100)
    if fill_w > 0:
        M5.Lcd.fillRect(bx + 2, y + 2, fill_w, body_h - 4, BLACK)
    _use(M5.Lcd.FONTS.Montserrat16, BLACK)
    M5.Lcd.drawString("{}%".format(pct), bx - 52, y + 2)


def render_day_heading(date_str, y):
    _use(M5.Lcd.FONTS.Montserrat18, BLACK)
    M5.Lcd.drawString(format_date_heading(date_str), MARGIN, y)
    return y + 30


def render_event(event, y):
    time_label = "All day" if event.get("all_day") else format_time(event["start"])
    _use(M5.Lcd.FONTS.Montserrat24, BLACK)
    M5.Lcd.drawString(time_label, MARGIN, y)
    M5.Lcd.drawString(truncate(event["title"], TITLE_MAX_CHARS), MARGIN + TIME_COL_W, y)
    detail = format_detail_line(event)
    if detail:
        _use(M5.Lcd.FONTS.Montserrat16, GREY)
        M5.Lcd.drawString(detail, MARGIN + TIME_COL_W, y + 34)
        return y + 64
    return y + 42


def format_clock(t):
    """time tuple -> 'HH:MM'."""
    return "{:02d}:{:02d}".format(t[3], t[4])


def render_footer(last_updated, battery_pct, warning=None):
    y = HEIGHT - FOOTER_H
    M5.Lcd.drawLine(MARGIN, y, WIDTH - MARGIN, y, BLACK)
    _use(M5.Lcd.FONTS.Montserrat16, GREY)
    text = "Updated {}".format(last_updated)
    if warning:
        text += "  ! {}".format(warning)
    M5.Lcd.drawString(text, MARGIN, y + 14)
    _draw_battery(WIDTH - MARGIN, y + 12, battery_pct)


def render_all(events, battery_pct, last_updated, warning=None):
    """Full-screen refresh: day-grouped events, footer with battery."""
    M5.Lcd.setRotation(0)
    M5.Lcd.fillScreen(WHITE)
    y = MARGIN
    for date_str, day_events in group_events_by_day(events):
        y = render_day_heading(date_str, y)
        for event in day_events:
            y = render_event(event, y)
        y += 12
    render_footer(last_updated, battery_pct, warning)


def render_error(title, detail, battery_pct):
    """Full-screen error state (no WiFi / auth failure / unreachable API)."""
    M5.Lcd.setRotation(0)
    M5.Lcd.fillScreen(WHITE)
    _use(M5.Lcd.FONTS.Montserrat40, BLACK)
    M5.Lcd.drawString(title, MARGIN, 360)
    _use(M5.Lcd.FONTS.Montserrat18, GREY)
    M5.Lcd.drawString(detail, MARGIN, 420)
    render_footer("", battery_pct)
