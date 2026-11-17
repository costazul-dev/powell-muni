from pathlib import Path

import pytest
from PIL import Image

from display.image import load_image
from display.render import draw_image

FIXTURE = Path(__file__).parent / "fixtures" / "image_sample.png"

RED = (255, 0, 0)
BLUE = (0, 0, 255)


class FakeCanvas:
    def __init__(self):
        self.pixels = []

    def SetPixel(self, x, y, r, g, b):
        self.pixels.append((x, y, r, g, b))


def test_load_image_returns_rgba_fixture():
    image = load_image(str(FIXTURE))

    assert image.mode == "RGBA"
    assert image.width == 4
    assert image.height == 3


def test_load_image_converts_rgb_to_rgba(tmp_path):
    path = tmp_path / "rgb.png"
    Image.new("RGB", (2, 2), (10, 20, 30)).save(path)

    image = load_image(str(path))

    assert image.mode == "RGBA"
    assert image.getpixel((0, 0)) == (10, 20, 30, 255)


@pytest.mark.parametrize("size", [(129, 64), (128, 65)])
def test_load_image_rejects_image_larger_than_panel(tmp_path, size):
    path = tmp_path / "large.png"
    Image.new("RGBA", size).save(path)

    with pytest.raises(ValueError):
        load_image(str(path))


def test_load_image_accepts_full_panel_size(tmp_path):
    path = tmp_path / "full.png"
    Image.new("RGBA", (128, 64)).save(path)

    assert load_image(str(path)).size == (128, 64)


def test_draw_image_draws_only_opaque_pixels_offset_by_position():
    canvas = FakeCanvas()

    draw_image(canvas, load_image(str(FIXTURE)), 10, 20)

    expected = [(10 + col, 20, *RED) for col in range(4)]
    expected += [(10, 21, *RED), (13, 21, *BLUE)]
    expected += [(10 + col, 22, *BLUE) for col in range(4)]
    assert canvas.pixels == expected
