"""Load PNG pixel art from `assets/` for drawing on the LED matrix.

Assets are exported at 1x scale, so one image pixel is one LED.
"""

from PIL import Image

from display.render import PANEL_HEIGHT, PANEL_WIDTH


def load_image(path: str) -> Image.Image:
    """The PNG at `path` as `RGBA`; raises `ValueError` if it is larger than the panel."""
    with Image.open(path) as source:
        image = source.convert("RGBA")
    if image.width > PANEL_WIDTH or image.height > PANEL_HEIGHT:
        raise ValueError(
            f"{path} is {image.width}x{image.height}; the panel is {PANEL_WIDTH}x{PANEL_HEIGHT}"
        )
    return image
