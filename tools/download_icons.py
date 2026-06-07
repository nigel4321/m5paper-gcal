"""Download OpenWeatherMap icons and convert them to high-contrast B&W for e-ink.

Run once (or whenever you want to refresh the icon set). The processed PNGs are
saved to src/icons/ and should be uploaded to /flash/icons/ on the device.

Usage:
    python tools/download_icons.py

The device's ensure_icon() checks /flash/icons/<code>.png before downloading,
so pre-uploading these processed icons means the device never has to fetch them
(and avoids the light-grey color rendering that raw OWM PNGs give on e-ink).
"""
import os
import sys

import requests
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

ICON_URL = "http://openweathermap.org/img/wn/{}@2x.png"
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "src", "icons")

# All OWM icon codes we map WMO weather codes to (day + night variants)
CODES = [
    "01d", "01n",  # clear sky
    "02d", "02n",  # few clouds / partly cloudy
    "04d", "04n",  # broken / overcast
    "09d", "09n",  # shower rain
    "10d", "10n",  # rain
    "11d", "11n",  # thunderstorm
    "13d", "13n",  # snow
    "50d", "50n",  # mist / fog
]

# Luminance threshold: pixels darker than this become black, the rest white.
# OWM cloud bodies sit around 160-200 luminance; rain/lightning/snow are darker.
THRESHOLD = 180


def _convert(raw_bytes):
    """Convert a raw OWM PNG (color, RGBA) to a high-contrast grayscale PNG."""
    from io import BytesIO
    img = Image.open(BytesIO(raw_bytes)).convert("RGBA")
    r, g, b, a = img.split()
    grey = img.convert("L")
    bw = grey.point(lambda v: 0 if v < THRESHOLD else 255, "L")
    # Transparent areas (alpha < 128) -> white
    result = Image.new("L", img.size, 255)
    result.paste(bw, mask=a)
    out = BytesIO()
    result.save(out, format="PNG")
    return out.getvalue()


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for code in CODES:
        url = ICON_URL.format(code)
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            print("SKIP {} — HTTP {}".format(code, resp.status_code))
            continue
        processed = _convert(resp.content)
        path = os.path.join(OUT_DIR, code + ".png")
        with open(path, "wb") as f:
            f.write(processed)
        print("wrote", path)


if __name__ == "__main__":
    main()
