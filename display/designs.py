"""The five candidate layouts from `docs/LayoutSpecs.md`, drawn from showcase `Card`s.

Every layout function takes `(canvas, backend, fonts, icons, cards, active, colors, stale)`,
clears the canvas, and draws one full frame. Text `y` values are baselines, as in
`graphics.DrawText`.
"""

from pathlib import Path
from types import ModuleType

from display.image import load_image
from display.render import draw_image, text_width, to_color
from display.showcase import SAMPLE_CARDS, Card

ICONS_DIR = Path(__file__).resolve().parent.parent / "assets" / "icons"
ICON_BODY_RGB = ((0, 90, 200), (220, 30, 30))
ICON_FILES = {
    ("bus", "32x34"): "bus_32x34_blue.png",
    ("rail", "32x34"): "rail_32x34_red.png",
    ("bus", "13x15"): "bus_13x15_blue.png",
    ("rail", "13x15"): "rail_13x15_red.png",
}
MODE_LABELS = {"bus": "Bus", "rail": "Metro"}
BOARD_ROWS_Y = (0, 22, 43)
STRIP_ROWS_Y = (41, 53)
PAGER_SPACING = 4
PANEL_RIGHT = 127


def recolor_icon(image, rgb):
    """A copy of the RGBA `image` with blue and red body pixels set to `rgb`, alpha kept."""
    fill = tuple(rgb)
    recolored = image.copy()
    recolored.putdata([
        (*fill, a) if (r, g, b) in ICON_BODY_RGB else (r, g, b, a)
        for r, g, b, a in image.getdata()
    ])
    return recolored


def load_icons(colors: dict) -> dict:
    """Recolored icons keyed by `(mode, size, color_name)` for every mode and color in `SAMPLE_CARDS`."""
    images = {key: load_image(str(ICONS_DIR / name)) for key, name in ICON_FILES.items()}
    used = {(card.mode, card.color) for card in SAMPLE_CARDS}
    return {
        (mode, size, color): recolor_icon(images[(mode, size)], colors[color])
        for (mode, color) in used
        for (icon_mode, size) in images
        if icon_mode == mode
    }


def fill_rect(canvas, x: int, y: int, width: int, height: int, rgb) -> None:
    """Filled rectangle in `rgb` with its top-left at (`x`, `y`)."""
    for row in range(y, y + height):
        for col in range(x, x + width):
            canvas.SetPixel(col, row, *rgb)


def draw_text(canvas, backend: ModuleType, font, x: int, y: int, rgb, text: str) -> int:
    """`text` with its baseline at `y`; returns the x just past it."""
    backend.graphics.DrawText(canvas, font, x, y, to_color(backend, rgb), text)
    return x + text_width(font, text)


def draw_centered(canvas, backend: ModuleType, font, box: tuple[int, int, int, int], color, text: str) -> None:
    """`text` centered in `box` `(x, y, w, h)` by the spec's formula, in `color` (`[r, g, b]`)."""
    x, y, w, h = box
    text_x = x + (w - text_width(font, text)) // 2
    baseline = y + (h + font.baseline - 1) // 2
    draw_text(canvas, backend, font, text_x, baseline, color, text)


def draw_times(canvas, backend: ModuleType, font, x: int, y: int, minutes, colors: dict, stale: bool) -> None:
    """`2 min  10  23`: first time white, the rest gray, or the whole row yellow when `stale`."""
    if not minutes:
        return
    first = colors["yellow"] if stale else colors["white"]
    rest = colors["yellow"] if stale else colors["gray"]
    x = draw_text(canvas, backend, font, x, y, first, str(minutes[0]))
    later = "".join(f"  {minute}" for minute in minutes[1:])
    draw_text(canvas, backend, font, x, y, rest, " min" + later)


def draw_pager(canvas, x: int, y: int, count: int, active: int, colors: dict) -> None:
    """`count` 2x2 dots from (`x`, `y`), 4 px apart; the `active` one white, the rest dim."""
    for index in range(count):
        rgb = colors["white"] if index == active else colors["dim"]
        fill_rect(canvas, x + index * PAGER_SPACING, y, 2, 2, rgb)


def draw_line_badge(canvas, backend: ModuleType, font, x: int, y: int, height: int, baseline: int, card: Card, colors: dict) -> int:
    """Line badge sized to its text plus 2 px each side; returns the x just past it."""
    width = text_width(font, card.line) + 4
    fill_rect(canvas, x, y, width, height, colors[card.color])
    draw_text(canvas, backend, font, x + 2, baseline, colors["white"], card.line)
    return x + width


def draw_flight_card(canvas, backend: ModuleType, fonts: dict, icons: dict, cards, active: int, colors: dict, stale: bool) -> None:
    """Layout A: one line per screen with a large badge and pager."""
    canvas.Clear()
    card = cards[active]
    main = fonts["6x10"]
    fill_rect(canvas, 0, 0, 38, 34, colors[card.color])
    draw_centered(canvas, backend, fonts["10x20"], (0, 0, 38, 28), colors["white"], card.line)
    draw_pager(canvas, 14, 28, len(cards), active, colors)
    draw_text(canvas, backend, main, 44, 9, colors["white"], card.route_name)
    draw_text(canvas, backend, main, 44, 21, colors["gray"], card.direction)
    draw_text(canvas, backend, main, 44, 33, colors["gray"], card.stop_name)
    draw_text(canvas, backend, main, 1, 47, colors["white"], f"to {card.destination}")
    draw_times(canvas, backend, main, 1, 59, card.minutes, colors, stale)


def draw_departures_board(canvas, backend: ModuleType, fonts: dict, icons: dict, cards, active: int, colors: dict, stale: bool) -> None:
    """Layout B: every line at once, badge on the left."""
    canvas.Clear()
    for card, y in zip(cards, BOARD_ROWS_Y):
        fill_rect(canvas, 0, y, 20, 19, colors[card.color])
        numeral = fonts["6x10"] if len(card.line) >= 3 else fonts["7x13B"]
        draw_centered(canvas, backend, numeral, (0, y, 20, 19), colors["white"], card.line)
        draw_text(canvas, backend, fonts["5x8"], 24, y + 7, colors["gray"], f"to {card.destination}")
        draw_times(canvas, backend, fonts["6x10"], 24, y + 18, card.minutes, colors, stale)


def draw_hero_strip(canvas, backend: ModuleType, fonts: dict, icons: dict, cards, active: int, colors: dict, stale: bool) -> None:
    """Layout C: the active line large on top, the other lines in a strip below."""
    canvas.Clear()
    card = cards[active]
    main = fonts["6x10"]
    fill_rect(canvas, 0, 0, 30, 30, colors[card.color])
    draw_centered(canvas, backend, fonts["10x20"], (0, 0, 30, 26), colors["white"], card.line)
    draw_pager(canvas, 10, 26, len(cards), active, colors)
    draw_text(canvas, backend, main, 35, 8, colors["white"], card.route_name)
    draw_text(canvas, backend, fonts["5x8"], 35, 17, colors["gray"], f"to {card.destination}")

    next_rgb = colors["yellow"] if stale else colors["white"]
    rest_rgb = colors["yellow"] if stale else colors["gray"]
    if card.minutes:
        x = draw_text(canvas, backend, fonts["9x18B"], 35, 31, next_rgb, str(card.minutes[0]))
        draw_text(canvas, backend, main, x + 2, 31, rest_rgb, "min")
        later = "  ".join(str(minute) for minute in card.minutes[1:])
        if later:
            draw_text(canvas, backend, main, PANEL_RIGHT - text_width(main, later), 31, rest_rgb, later)

    for x in range(0, PANEL_RIGHT + 1, 2):
        canvas.SetPixel(x, 37, *colors["dim"])

    others = [other for index, other in enumerate(cards) if index != active]
    for other, y in zip(others, STRIP_ROWS_Y):
        fill_rect(canvas, 0, y, 15, 10, colors[other.color])
        draw_centered(canvas, backend, main, (0, y, 15, 10), colors["white"], other.line)
        draw_times(canvas, backend, main, 19, y + 8, other.minutes, colors, stale)


def draw_icon_card(canvas, backend: ModuleType, fonts: dict, icons: dict, cards, active: int, colors: dict, stale: bool) -> None:
    """Layout D: layout A with a vehicle icon in place of the large badge."""
    canvas.Clear()
    card = cards[active]
    main = fonts["6x10"]
    draw_image(canvas, icons[(card.mode, "32x34", card.color)], 3, 0)
    badge_end = draw_line_badge(canvas, backend, main, 44, 0, 11, 9, card, colors)
    draw_text(canvas, backend, main, badge_end + 3, 9, colors["gray"], MODE_LABELS[card.mode])
    draw_pager(canvas, 116, 1, len(cards), active, colors)
    draw_text(canvas, backend, main, 44, 21, colors["white"], card.route_name)
    draw_text(canvas, backend, main, 44, 33, colors["gray"], card.stop_name)
    draw_text(canvas, backend, main, 1, 47, colors["white"], f"to {card.destination}")
    draw_times(canvas, backend, main, 1, 59, card.minutes, colors, stale)


def draw_icon_board(canvas, backend: ModuleType, fonts: dict, icons: dict, cards, active: int, colors: dict, stale: bool) -> None:
    """Layout E: layout B with a small vehicle icon beside each line badge."""
    canvas.Clear()
    small = fonts["5x8"]
    for card, y in zip(cards, BOARD_ROWS_Y):
        draw_image(canvas, icons[(card.mode, "13x15", card.color)], 0, y + 2)
        badge_end = draw_line_badge(canvas, backend, small, 17, y, 9, y + 7, card, colors)
        draw_text(canvas, backend, small, badge_end + 3, y + 7, colors["gray"], f"to {card.destination}")
        draw_times(canvas, backend, fonts["6x10"], 17, y + 19, card.minutes, colors, stale)


DESIGNS = {
    "A": draw_flight_card,
    "B": draw_departures_board,
    "C": draw_hero_strip,
    "D": draw_icon_card,
    "E": draw_icon_board,
}
