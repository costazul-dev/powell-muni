"""Draw display rows on the LED matrix through an emulator or hardware backend.

`RGBMatrixEmulator` mirrors the `rgbmatrix` API, so every function here takes the
backend module as an argument and the drawing code is the same on macOS and the Pi.
"""

import importlib
from types import ModuleType

from display.layout import Row

BACKEND_MODULES = {
    "emulator": "RGBMatrixEmulator",
    "hardware": "rgbmatrix",
}

PANEL_HEIGHT = 64
BADGE_PADDING = 2
BADGE_GAP = 3
BADGE_TEXT_RGB = [255, 255, 255]


def load_backend(name: str) -> ModuleType:
    """The matrix module for `"emulator"` or `"hardware"`; imported here because `rgbmatrix` only exists on the Pi."""
    if name not in BACKEND_MODULES:
        raise ValueError(f"unknown display backend {name!r}; expected one of {sorted(BACKEND_MODULES)}")
    return importlib.import_module(BACKEND_MODULES[name])


def create_matrix(backend: ModuleType, display_config: dict):
    """An `RGBMatrix` configured from `display.hardware` and `display.brightness`."""
    hardware = display_config["hardware"]
    options = backend.RGBMatrixOptions()
    options.rows = hardware["rows"]
    options.cols = hardware["cols"]
    options.hardware_mapping = hardware["hardware_mapping"]
    options.gpio_slowdown = hardware["gpio_slowdown"]
    options.brightness = display_config["brightness"]
    return backend.RGBMatrix(options=options)


def load_font(backend: ModuleType, path: str):
    """A BDF font loaded from `path`."""
    font = backend.graphics.Font()
    font.LoadFont(path)
    return font


def to_color(backend: ModuleType, rgb: list[int]):
    """A backend `Color` from an `[r, g, b]` triple."""
    return backend.graphics.Color(*rgb)


def text_width(font, text: str) -> int:
    """Pixel width of `text` in `font`."""
    return sum(font.CharacterWidth(ord(char)) for char in text)


def draw_badge(canvas, backend: ModuleType, font, x: int, y: int, line: str, rgb: list[int]) -> int:
    """Filled rectangle in `rgb` with the route in white, top-left at (`x`, `y`); returns the badge width."""
    width = text_width(font, line) + 2 * BADGE_PADDING
    fill = to_color(backend, rgb)
    for row_y in range(y, y + font.height):
        backend.graphics.DrawLine(canvas, x, row_y, x + width - 1, row_y, fill)
    backend.graphics.DrawText(
        canvas, font, x + BADGE_PADDING, y + font.baseline, to_color(backend, BADGE_TEXT_RGB), line
    )
    return width


def draw_row(canvas, backend: ModuleType, font, y: int, row: Row, colors: dict) -> None:
    """Badge at the left edge, then `row.text` in `colors[row.text_color]`, with the row's top at `y`."""
    badge_width = draw_badge(canvas, backend, font, 0, y, row.line, colors[row.badge_color])
    backend.graphics.DrawText(
        canvas, font, badge_width + BADGE_GAP, y + font.baseline, to_color(backend, colors[row.text_color]), row.text
    )


def draw_rows(canvas, backend: ModuleType, font, rows: list[Row], colors: dict) -> None:
    """Clear the canvas and draw each row in an equal share of the panel height."""
    canvas.Clear()
    if not rows:
        return
    row_height = PANEL_HEIGHT // len(rows)
    for index, row in enumerate(rows):
        draw_row(canvas, backend, font, index * row_height, row, colors)


def show(matrix, canvas):
    """Swap `canvas` onto the panel; returns the next canvas to draw on."""
    return matrix.SwapOnVSync(canvas)
