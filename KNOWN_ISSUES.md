# Known Issues

(none open)

## Resolved

### Display inversion at bottom of screen — fixed

**Cause:** the ellipsis character `…` (U+2026) appended by `display.truncate()`
when an event title was longer than `TITLE_MAX_CHARS`. The M5GFX Montserrat
font on the device had no glyph for this codepoint, and the rendered fallback
caused inversion artefacts on the affected row (and sometimes the rows above).

**Fix:** `display.truncate()` now hard-cuts at `max_chars` with no ellipsis
appended (`src/display.py`). Once `…` was gone from the rendered text, the
inverted last-row regression stopped reproducing.

We had also tried, before the real cause was found, the following — all of
which were red herrings and have been reverted:

- single-arg vs two-arg `setTextColor`
- `setEpdMode(EPD_QUALITY)` + `clear(WHITE)` at start of `render_all`
- single-font (Montserrat40 everywhere) vs multi-font layout
- per-`drawString` state reset via the `_draw` helper

The `_draw` helper is still in place defensively (it makes the rendering
code more predictable) but is not load-bearing for the inversion fix.
