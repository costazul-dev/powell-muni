import pytest
from PIL import Image

from display.designs import recolor_icon
from display.showcase import showcase_frame

BUS_BLUE = (0, 90, 200)
RAIL_RED = (220, 30, 30)
FIXED = [(255, 200, 0), (255, 255, 255), (120, 120, 120), (60, 60, 60), (0, 0, 0)]


@pytest.mark.parametrize(
    "elapsed, expected",
    [(0, ("A", 0)), (15, ("B", 0)), (75, ("A", 0))],
)
def test_showcase_frame_cycles_layouts(elapsed, expected):
    assert showcase_frame(elapsed, 15, 5, None) == expected


@pytest.mark.parametrize("elapsed, active", [(0, 0), (5, 1), (10, 2), (15, 0)])
def test_showcase_frame_rotates_active_card(elapsed, active):
    assert showcase_frame(elapsed, 15, 5, None)[1] == active


@pytest.mark.parametrize("elapsed", [0, 15, 40, 75])
def test_showcase_frame_holds_pinned_layout(elapsed):
    assert showcase_frame(elapsed, 15, 5, "C")[0] == "C"


def test_recolor_icon_replaces_body_pixels_and_keeps_accents():
    pixels = [(*BUS_BLUE, 255), (*RAIL_RED, 128)] + [(*rgb, 255) for rgb in FIXED]
    image = Image.new("RGBA", (len(pixels), 1))
    image.putdata(pixels)

    recolored = recolor_icon(image, [10, 20, 30])

    assert list(recolored.getdata()) == [(10, 20, 30, 255), (10, 20, 30, 128)] + pixels[2:]
    assert list(image.getdata()) == pixels
