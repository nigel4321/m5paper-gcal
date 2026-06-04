"""Render the M5Paper display layout to a PNG for local preview.

Usage:
    python tools/preview.py                     # MOCK_EVENTS, writes preview.png
    python tools/preview.py --live              # real events via src/config.py
    python tools/preview.py --events events.json # events from a JSON file
    python tools/preview.py --open               # also open the PNG (macOS)

Mirrors the layout in src/display.py: 540x960 portrait, day headings,
time + title rows, footer with "Updated HH:MM" and a battery glyph.
Fonts fall back through Montserrat (if installed) -> Helvetica -> Arial
-> PIL default, so output looks close but won't be pixel-identical to
the device's M5GFX Montserrat rendering.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from unittest.mock import MagicMock

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
# Stub device-only modules so we can import src.display / src.calendar on the host
sys.modules["M5"] = MagicMock()
from src import calendar as C  # noqa: E402
from src import display as D  # noqa: E402
from src.mock_data import MOCK_EVENTS  # noqa: E402


def _fetch_live_events(max_results):
    """Pull real events from Google Calendar using src/config.py credentials."""
    try:
        from src import config
    except ImportError as e:
        raise SystemExit(
            "src/config.py not found — copy src/config.example.py to src/config.py "
            "and fill in CLIENT_ID / CLIENT_SECRET / REFRESH_TOKEN. ({})".format(e)
        )
    token = C.refresh_access_token(config.CLIENT_ID, config.CLIENT_SECRET, config.REFRESH_TOKEN)
    n = max_results if max_results is not None else getattr(config, "MAX_EVENTS", 5)
    return C.get_upcoming_events(token, n)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

FONT_CANDIDATES = [
    "/Library/Fonts/Montserrat-Regular.ttf",
    "/Users/{}/Library/Fonts/Montserrat-Regular.ttf".format(os.environ.get("USER", "")),
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def _load_font(size):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def render(events, battery_pct, last_updated, warning=None):
    img = Image.new("L", (D.WIDTH, D.HEIGHT), 255)
    draw = ImageDraw.Draw(img)

    f_day = _load_font(24)
    f_event = _load_font(40)
    f_footer = _load_font(24)
    f_battery = _load_font(18)

    y = D.MARGIN
    for date_str, day_events in D.group_events_by_day(events):
        draw.text((D.MARGIN, y), D.format_date_heading(date_str), fill=0, font=f_day)
        y += 40
        for event in day_events:
            time_label = "All day" if event.get("all_day") else D.format_time(event["start"])
            draw.text((D.MARGIN, y), time_label, fill=0, font=f_event)
            draw.text(
                (D.MARGIN + D.TIME_COL_W, y),
                D.truncate(event["title"], D.TITLE_MAX_CHARS),
                fill=0,
                font=f_event,
            )
            y += 60
        y += 20

    fy = D.HEIGHT - D.FOOTER_H
    draw.line([(D.MARGIN, fy), (D.WIDTH - D.MARGIN, fy)], fill=0, width=1)
    text = "Updated {}".format(last_updated)
    if warning:
        text += "  ! {}".format(warning)
    draw.text((D.MARGIN, fy + 18), text, fill=0, font=f_footer)

    # Battery glyph (matches display._draw_battery)
    body_w, body_h = 52, 28
    bx = D.WIDTH - D.MARGIN - body_w
    by = fy + 16
    draw.rectangle([bx, by, bx + body_w - 1, by + body_h - 1], outline=0, width=1)
    draw.rectangle([D.WIDTH - D.MARGIN, by + 8, D.WIDTH - D.MARGIN + 3, by + 19], fill=0)
    fill_w = int((body_w - 4) * max(0, min(100, battery_pct)) / 100)
    if fill_w > 0:
        draw.rectangle([bx + 2, by + 2, bx + 2 + fill_w - 1, by + body_h - 2 - 1], fill=0)
    draw.text((bx - 60, by + 4), "{}%".format(battery_pct), fill=0, font=f_battery)

    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="Fetch real events from Google Calendar")
    ap.add_argument("--events", help="Path to a JSON file of events (defaults to MOCK_EVENTS)")
    ap.add_argument("--max", type=int, default=None, help="Max events when using --live")
    ap.add_argument("--battery", type=int, default=84)
    ap.add_argument("--updated", default=None, help="HH:MM (defaults to now)")
    ap.add_argument("--warning", default=None)
    ap.add_argument("--out", default="preview.png")
    ap.add_argument("--open", action="store_true", help="Open the PNG when done")
    args = ap.parse_args()

    if args.live:
        events = _fetch_live_events(args.max)
    elif args.events:
        with open(args.events) as f:
            events = json.load(f)
    else:
        events = MOCK_EVENTS

    updated = args.updated or "{:02d}:{:02d}".format(time.localtime().tm_hour, time.localtime().tm_min)

    img = render(events, args.battery, updated, warning=args.warning)
    img.save(args.out)
    print("wrote", args.out)

    if args.open:
        subprocess.run(["open", args.out], check=False)


if __name__ == "__main__":
    main()
