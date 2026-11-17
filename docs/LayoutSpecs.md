# powell-muni Layout Specs

Five layouts for the 128x64 HUB75 panel. Every coordinate is in LED pixels; origin (0,0) is top-left.

## Folder Contents

| Folder | Contents |
|---|---|
| `tests/fixtures/layouts/` | Exact 128x64 frames, one pixel per LED. Use as golden images for snapshot tests. |
| `docs/layouts/` | Same frames rendered as an LED panel (8x scale) for viewing. |
| `assets/icons/` | Vehicle marks for layouts D and E at 1x. |
| `fonts/` | BDF fonts used by the layouts, from hzeller/rpi-rgb-led-matrix `fonts/`. |

The data in every frame is sample data: destinations, stop names, and times are placeholders.

## Conventions

- Text coordinates are the **baseline** `y`, as in `graphics.DrawText(canvas, font, x, y, color, text)`.
- "Centered in box (x, y, w, h)": `text_x = x + (w - text_width) // 2`, `baseline = y + (h + font_ascent - 1) // 2`.
- Times row: first time in white, then `" min"` in gray, then each later time prefixed by two spaces, in gray. Example: `2 min  10  23`.
- Stale data (no successful fetch within 2x the fetch interval): the times row is drawn entirely in yellow.
- Pager dots: 2x2 squares spaced 4 px apart; the active line's dot is white, the others dim.

## Colors (RGB)

| Name | Value | Use |
|---|---|---|
| blue | 0, 90, 200 | Bus line badges and icons |
| red | 220, 30, 30 | Muni Metro badges and icons |
| white | 255, 255, 255 | Primary text, badge text, headlights |
| gray | 120, 120, 120 | Secondary text, wheels, rails |
| dim | 60, 60, 60 | Inactive pager dots, divider |
| yellow | 255, 200, 0 | Stale times; destination sign in icons |

## Fonts

| Font | Used for |
|---|---|
| 6x10 | Main text in every layout |
| 5x8 | Destinations in B, C, E; badges in E |
| 10x20 | Badge numerals in A, C |
| 7x13B | Badge numerals in B |
| 9x18B | Next-arrival countdown in C |

## Data Fields Needed

Arrivals currently carry only line, stop code, and expected time. These layouts also use the following fields from `MonitoredStopVisit[].MonitoredVehicleJourney`:

| Field | Shown as | Layouts |
|---|---|---|
| `PublishedLineName` | Route name ("Union-Stockton") | A, C, D |
| `DestinationName` | "to <destination>" | A, B, C, D, E |
| `MonitoredCall.StopPointName` | Stop name | A, D |
| `DirectionRef` | Direction ("Inbound") | A |

## A · Flight Card (rotating, one line per screen)

| Element | Spec |
|---|---|
| Badge | Filled rect (0, 0, 38x34), line color |
| Badge numeral | 10x20, white, centered in box (0, 0, 38, 28) |
| Pager | 3 dots at y=28, x=14, 18, 22 |
| Route name | 6x10, white, x=44, baseline 9 |
| Direction | 6x10, gray, x=44, baseline 21 |
| Stop name | 6x10, gray, x=44, baseline 33 |
| Destination | 6x10, white, x=1, baseline 47 |
| Times | 6x10, x=1, baseline 59 |

The right column is 84 px wide (14 characters of 6x10).

## B · Departures Board (static, all lines)

Rows start at y = 0, 22, 43 (row pitch 21, +1 after the first row).

| Element | Spec |
|---|---|
| Badge | Filled rect (0, y, 20x19), line color |
| Badge numeral | 7x13B (6x10 if 3+ characters), white, centered in box (0, y, 20, 19) |
| Destination | 5x8, gray, x=24, baseline y+7 |
| Times | 6x10, x=24, baseline y+18 |

## C · Hero + Strip (rotating featured line)

| Element | Spec |
|---|---|
| Badge | Filled rect (0, 0, 30x30), line color |
| Badge numeral | 10x20, white, centered in box (0, 0, 30, 26) |
| Pager | 3 dots at y=26, x=10, 14, 18 |
| Route name | 6x10, white, x=35, baseline 8 |
| Destination | 5x8, gray, x=35, baseline 17 |
| Next time | 9x18B, white, x=35, baseline 31 |
| "min" | 6x10, gray, 2 px after next time, baseline 31 |
| Later times | 6x10, gray, right-aligned to x=127, baseline 31, two spaces between |
| Divider | Dim pixel every 2 px along y=37 |
| Strip rows | y = 41, 53: badge rect (0, y, 15x10), 6x10 numeral centered; times 6x10 at x=19, baseline y+8 |

## D · Icon Card (rotating, variant of A)

| Element | Spec |
|---|---|
| Vehicle icon | `assets/icons/bus_32x34_*` or `assets/icons/rail_32x34_*` drawn at (3, 0) |
| Line badge | Rect at (44, 0), width = text width + 4, height 11, line color; 6x10 white text at x+2, baseline 9 |
| Mode label | "Bus" / "Metro", 6x10, gray, 3 px after badge, baseline 9 |
| Pager | 3 dots at y=1, x=116, 120, 124 |
| Route name | 6x10, white, x=44, baseline 21 |
| Stop name | 6x10, gray, x=44, baseline 33 |
| Destination | 6x10, white, x=1, baseline 47 |
| Times | 6x10, x=1, baseline 59 |

## E · Icon Board (static, variant of B)

Rows start at y = 0, 22, 43.

| Element | Spec |
|---|---|
| Vehicle icon | `assets/icons/bus_13x15_*` or `assets/icons/rail_13x15_*` drawn at (0, y+2) |
| Line badge | Rect at (17, y), width = text width + 4, height 9, line color; 5x8 white text at x+2, baseline y+7 |
| Destination | 5x8, gray, 3 px after badge, baseline y+7 |
| Times | 6x10, x=17, baseline y+19 |

## Icons

The icon PNGs are drawn in a specific line color (blue bus, red rail). In code, recolor the body pixels to the row's line color. Keep the fixed accents as they are: yellow sign, white headlights, gray wheels, pantograph and rails. Black pixels are unlit.

## Rotation (A, C, D)

Switch to the next line on a fixed interval, for example 5 seconds. Keep this separate from the fetch interval. The pager dot follows the line on screen.
