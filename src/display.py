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
FOOTER_H = 60
TIME_COL_W = 140
TITLE_MAX_CHARS = 16
ICON_SIZE = 100
ICON_DIR = "/flash/icons"

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


def format_weekday(date_str):
    """'2026-05-30' -> 'Saturday'."""
    y, m, d = int(date_str[:4]), int(date_str[5:7]), int(date_str[8:10])
    return _WEEKDAYS[day_of_week(y, m, d)]


def format_day_month(date_str):
    """'2026-05-30' -> '30 May'."""
    m, d = int(date_str[5:7]), int(date_str[8:10])
    return "{} {}".format(d, _MONTHS[m - 1])


def format_time(start):
    """'2026-05-30T09:00:00' -> '09:00'."""
    return start[11:16]


def truncate(text, max_chars):
    if len(text) <= max_chars:
        return text
    return text[:max_chars]


_DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def _days_in_month(y, m):
    if m == 2 and ((y % 4 == 0 and y % 100 != 0) or y % 400 == 0):
        return 29
    return _DAYS_IN_MONTH[m - 1]


def _last_sunday(y, m):
    last = _days_in_month(y, m)
    return last - day_of_week(y, m, last)  # day_of_week: 0=Sunday


def _london_offset_hours(utc_t):
    """0 = GMT, 1 = BST. UK rule: last Sun Mar 01:00 UTC -> BST; last Sun Oct 01:00 UTC -> GMT."""
    y, m, d, h = utc_t[0], utc_t[1], utc_t[2], utc_t[3]
    if m < 3 or m > 10:
        return 0
    if 3 < m < 10:
        return 1
    last_sun = _last_sunday(y, m)
    if m == 3:
        if d > last_sun or (d == last_sun and h >= 1):
            return 1
        return 0
    if d < last_sun or (d == last_sun and h < 1):
        return 1
    return 0


def to_london(utc_t):
    """UTC time tuple -> London local time tuple. Auto-handles BST/GMT each year."""
    offset = _london_offset_hours(utc_t)
    if offset == 0:
        return utc_t
    y, mo, d, h, mi, s = utc_t[0], utc_t[1], utc_t[2], utc_t[3], utc_t[4], utc_t[5]
    h += offset
    if h >= 24:
        h -= 24
        d += 1
        if d > _days_in_month(y, mo):
            d = 1
            mo += 1
            if mo > 12:
                mo = 1
                y += 1
    return (y, mo, d, h, mi, s, day_of_week(y, mo, d), 0)


def date_str_from_time(t):
    """Time tuple -> 'YYYY-MM-DD'."""
    return "{:04d}-{:02d}-{:02d}".format(t[0], t[1], t[2])


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

def _draw(font, text, x, y, color=BLACK):
    M5.Lcd.setFont(font)
    M5.Lcd.setTextSize(1)
    M5.Lcd.setTextColor(color, WHITE)
    M5.Lcd.drawString(text, x, y)


def _draw_battery(x, y, pct):
    """Battery glyph with proportional fill, right-aligned ending at x."""
    body_w, body_h = 52, 28
    bx = x - body_w
    M5.Lcd.drawRect(bx, y, body_w, body_h, BLACK)
    M5.Lcd.fillRect(x, y + 8, 4, 12, BLACK)  # terminal nub
    fill_w = int((body_w - 4) * max(0, min(100, pct)) / 100)
    if fill_w > 0:
        M5.Lcd.fillRect(bx + 2, y + 2, fill_w, body_h - 4, BLACK)
    _draw(M5.Lcd.FONTS.Montserrat18, "{}%".format(pct), bx - 60, y + 4)


def render_top_heading(date_str, y, weather_icon=None):
    """Two-line date on the left ('Saturday' / '6 June'), optional icon on the right."""
    _draw(M5.Lcd.FONTS.Montserrat40, format_weekday(date_str), MARGIN, y)
    _draw(M5.Lcd.FONTS.Montserrat24, format_day_month(date_str), MARGIN, y + 50)
    if weather_icon:
        try:
            M5.Lcd.drawPng(
                "{}/{}.png".format(ICON_DIR, weather_icon),
                WIDTH - MARGIN - ICON_SIZE,
                y,
            )
        except Exception as e:
            print("icon render failed:", e)
    line_y = y + 108
    M5.Lcd.drawLine(MARGIN, line_y, WIDTH - MARGIN, line_y, BLACK)
    return line_y + 18


def render_day_heading(date_str, y):
    _draw(M5.Lcd.FONTS.Montserrat24, format_date_heading(date_str), MARGIN, y)
    return y + 40


def render_event(event, y):
    time_label = "All day" if event.get("all_day") else format_time(event["start"])
    _draw(M5.Lcd.FONTS.Montserrat40, time_label, MARGIN, y)
    _draw(M5.Lcd.FONTS.Montserrat40, truncate(event["title"], TITLE_MAX_CHARS), MARGIN + TIME_COL_W, y)
    return y + 60


def format_clock(t):
    """time tuple -> 'HH:MM'."""
    return "{:02d}:{:02d}".format(t[3], t[4])


def render_footer(last_updated, battery_pct, warning=None):
    y = HEIGHT - FOOTER_H
    M5.Lcd.drawLine(MARGIN, y, WIDTH - MARGIN, y, BLACK)
    text = "Updated {}".format(last_updated)
    if warning:
        text += "  ! {}".format(warning)
    _draw(M5.Lcd.FONTS.Montserrat24, text, MARGIN, y + 18)
    _draw_battery(WIDTH - MARGIN, y + 16, battery_pct)


def render_all(events, battery_pct, last_updated, today=None, weather_icon=None, warning=None):
    """Full-screen refresh: today heading + weather icon, day-grouped events, footer."""
    M5.Lcd.setRotation(0)
    M5.Lcd.fillScreen(WHITE)
    y = MARGIN
    if today:
        y = render_top_heading(today, y, weather_icon=weather_icon)
    for date_str, day_events in group_events_by_day(events):
        y = render_day_heading(date_str, y)
        for event in day_events:
            y = render_event(event, y)
        y += 20
    render_footer(last_updated, battery_pct, warning)


def render_error(title, detail, battery_pct):
    """Full-screen error state (no WiFi / auth failure / unreachable API)."""
    M5.Lcd.setRotation(0)
    M5.Lcd.fillScreen(WHITE)
    _draw(M5.Lcd.FONTS.Montserrat48, title, MARGIN, 360)
    _draw(M5.Lcd.FONTS.Montserrat24, detail, MARGIN, 440)
    render_footer("", battery_pct)
