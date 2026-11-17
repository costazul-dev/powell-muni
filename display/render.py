"""Draw display rows on the LED matrix through an emulator or hardware backend.

`RGBMatrixEmulator` mirrors the `rgbmatrix` API, so every function here takes the
backend module as an argument and the drawing code is the same on macOS and the Pi.
"""

import importlib
from pathlib import Path
from types import ModuleType

from display.layout import Row

BACKEND_MODULES = {
    "emulator": "RGBMatrixEmulator",
    "hardware": "rgbmatrix",
}

PANEL_WIDTH = 128
PANEL_HEIGHT = 64
BADGE_PADDING = 2
BADGE_GAP = 3
BADGE_TEXT_RGB = [255, 255, 255]
FONTS_DIR = Path(__file__).resolve().parent.parent / "fonts"
LAYOUT_FONTS = ("6x10", "5x8", "10x20", "7x13B", "9x18B")


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


def load_fonts(backend: ModuleType) -> dict:
    """The layout fonts from `fonts/*.bdf`, keyed by name (`"6x10"`, `"5x8"`, ...)."""
    return {name: load_font(backend, str(FONTS_DIR / f"{name}.bdf")) for name in LAYOUT_FONTS}


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


def draw_image(canvas, image, x: int, y: int) -> None:
    """Draw an RGBA `image` with its top-left at (`x`, `y`), skipping fully transparent pixels.

    Pixels are set one at a time because `canvas.SetImage` drops the alpha mask; pixels off
    the panel are left to the backend's `SetPixel`, which ignores them.
    """
    for index, (r, g, b, a) in enumerate(image.getdata()):
        if a == 0:
            continue
        row, col = divmod(index, image.width)
        canvas.SetPixel(x + col, y + row, r, g, b)


def show(matrix, canvas):
    """Swap `canvas` onto the panel; returns the next canvas to draw on."""
    return matrix.SwapOnVSync(canvas)
