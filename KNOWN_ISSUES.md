# Known Issues

## Display inversion at bottom of screen

### Symptom
On the M5Paper, the last item or two rendered by `display.render_all`
appears as **white text on a black rectangle** instead of black text on
the e-ink grey background. Everything above it renders correctly.

In the most recent reproduction the inverted items were:
- the last event row (`12:30 Foulds Fair`)
- the day heading immediately above it (`Saturday 13 June`)
- the footer (`Updated 18:25`)

The break point is around the lower third of the panel; items above it
render fine.

### Environment
- M5Paper, UIFlow 2.0 MicroPython firmware
- `M5.Lcd` is an M5GFX `Display` object
- Available EPD modes: `EPD_FAST`, `EPD_FASTEST`, `EPD_QUALITY`, `EPD_TEXT`
  (current default: `EPD_TEXT`, value `1`)
- Available fonts include the full Montserrat family
  (`Montserrat12/14/16/18/24/40/44/48`) plus DejaVu, EFontCN/JA/KR, etc.

### What we ruled out

Each of these was tried in isolation and made **no difference** to the
inversion (or made it slightly worse, as noted):

| Hypothesis | What we tried | Result |
|---|---|---|
| `setTextColor(fg, bg)` two-arg form leaks state | Switched `_use` to single-arg `setTextColor(fg)` (transparent mode) | Inversion *spread*: the day heading above the affected event also went inverted |
| EPD partial-refresh residue at bottom of panel | `setEpdMode(EPDMode.EPD_QUALITY)` + `clear(WHITE)` at start of `render_all` | No change. (Did make the background look slightly more uniform grey though.) |
| State carries across `setFont` switches between Montserrat sizes | Used `Montserrat40` for **every** text element — no font switching at all during a render | No change |
| State carries across `drawString` calls within a row | Replaced "set state once per row" with `_draw(font, text, x, y)` that calls `setFont` + `setTextSize` + `setTextColor` immediately before **every** `drawString` | No change |
| Pure y-position triggers it | Drew "Test 40", "Test 200", "Test 400", "Test 600", "Test 800", "Test 900" with a single `setFont` / `setTextColor` and a 6-iteration `drawString` loop | All six rendered cleanly — so y-position alone is **not** the trigger |
| Custom font is required | n/a — earlier sanity-check code without `setFont` (default GLCD bitmap font, `setTextSize(4)`) rendered black-on-white correctly across the full screen | Single-font default-GLCD path works; multi-font M5GFX path doesn't |

### What we accepted (current state)
Reverted to the multi-font layout:
- Day heading: `Montserrat24`
- Time + event title: `Montserrat40`
- Footer "Updated HH:MM": `Montserrat24`
- Battery `%`: `Montserrat18`
- Error title: `Montserrat48`
- `_draw(font, text, x, y, color=BLACK)` helper sets font + size + colour
  per `drawString` (kept this defensively even though it didn't fix the
  inversion).

The inversion of the bottom rows is **shipping as-is**.

### Most likely next things to try
In rough order of how likely they are to actually fix it:

1. **Off-screen sprite render then `pushSprite`.** Allocate an
   `M5.Lcd.Sprite` (or `lgfx.LGFX_Sprite`), do all `drawString` calls
   into that sprite, then push the whole thing to the panel once. This
   bypasses whatever per-call state is going wrong in the direct-draw
   path. Medium-sized code change.
2. **Fill a `WHITE` rect for each text bounding box immediately after
   `drawString`, *then* re-draw the text on top.** Cheap to try, but
   only works if the inversion comes from drawString's bg fill (not a
   panel issue) and only one of the suspected modes.
3. **Try `M5.Lcd.print()` with `setCursor()` instead of
   `drawString()`.** Different LovyanGFX code path; may avoid whatever
   bg-fill bug `drawString` hits.
4. **Update / reflash the M5Paper firmware** to a newer UIFlow 2 build
   and re-test — this may be a firmware-side regression.

### Notes for whoever picks this up
- The bug is **deterministic** within a single render but **not**
  triggered by y-position alone (proven by the test pattern above).
  So the trigger is something about the *sequence* of calls in
  `render_all`, accumulated state across many `drawString` calls, or
  something position-dependent that only kicks in after certain prior
  state is set.
- A useful first probe is to bisect `render_all`: render only the first
  N items and see at which N the inversion appears. That would tell you
  whether it's the *Nth `drawString` overall* or *position past pixel Y*.
- The simple test pattern that worked is in this conversation's history;
  it should be the regression baseline for any future fix attempt.
