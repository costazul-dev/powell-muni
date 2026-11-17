from pathlib import Path

import pytest
import RGBMatrixEmulator as backend
import yaml

from display.designs import DESIGNS, load_icons
from display.render import PANEL_HEIGHT, PANEL_WIDTH, load_fonts
from display.showcase import SAMPLE_CARDS

CONFIG_EXAMPLE = Path(__file__).parent.parent / "config.yaml.example"


class FakeCanvas:
    width = PANEL_WIDTH
    height = PANEL_HEIGHT

    def __init__(self):
        self.pixels = []
        self.clears = 0

    def Clear(self):
        self.clears += 1

    def SetPixel(self, x, y, r, g, b):
        self.pixels.append((x, y, r, g, b))


@pytest.fixture(scope="module")
def colors():
    with open(CONFIG_EXAMPLE, encoding="utf-8") as file:
        return yaml.safe_load(file)["colors"]


@pytest.fixture(scope="module")
def fonts():
    return load_fonts(backend)


@pytest.fixture(scope="module")
def icons(colors):
    return load_icons(colors)


@pytest.mark.parametrize("stale", [False, True])
@pytest.mark.parametrize("key", sorted(DESIGNS))
def test_design_clears_and_draws(key, stale, fonts, icons, colors):
    canvas = FakeCanvas()

    DESIGNS[key](canvas, backend, fonts, icons, SAMPLE_CARDS, 0, colors, stale)

    assert canvas.clears >= 1
    assert canvas.pixels
