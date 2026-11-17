# powell-muni

## Overview

Polls the 511 SF Bay `StopMonitoring` API for three Muni lines and draws
departure countdowns on a 128x64 HUB75 RGB LED matrix (Adafruit product 6484)
driven by a Raspberry Pi.

| Row | Line | Mode       | Badge |
|-----|------|------------|-------|
| 1   | 45   | Bus        | Blue  |
| 2   | 1    | Bus        | Blue  |
| 3   | T    | Muni Metro | Red   |

Each row shows one direction, set by the configured `stop_code`.

## Repository Layout

```
main.py                  Orchestrator: load config, fetch, render, loop
transit/                 511 API access and response parsing
display/                 Layout and rendering on the LED matrix
display/designs.py       Candidate layouts A-E drawn from showcase cards
display/showcase.py      Sample cards and timing for showcase mode
assets/                  PNG pixel art drawn on the display
assets/icons/            Vehicle icons for layouts D and E
fonts/                   BDF fonts
tests/                   pytest suite
tests/fixtures/          Recorded API responses used by tests
tests/fixtures/layouts/  Exact 128x64 reference frames of the candidate layouts
docs/                    Reference material (511 API specification, Pi setup)
docs/LayoutSpecs.md      Coordinates, fonts, and colors of the candidate layouts
docs/layouts/            LED-style previews of the candidate layouts
deploy/                  systemd unit for the Pi
config.yaml.example      Example app config; copy to config.yaml
.env.example             Example secrets file; copy to .env
requirements.txt         Runtime dependencies
requirements-dev.txt     Runtime + development dependencies
```

`config.yaml` and `.env` are local-only and ignored by git.

## Local Development (macOS)

Requires Python 3.11 (the version shipped with Raspberry Pi OS Bookworm).
On macOS the display is rendered with `RGBMatrixEmulator` instead of real hardware.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

cp config.yaml.example config.yaml   # set stop codes; keep display.backend: emulator
cp .env.example .env                 # set API_511_KEY

python main.py                       # or: python main.py --config path/to/config.yaml
pytest
```

`main.py` logs to stdout. A failed fetch for a stop is logged and the previous
arrivals are kept; once they are older than twice the fetch interval the row's
times turn yellow.

511 keys are limited to 60 requests/hour by default. The fetch interval is
derived from the number of distinct stop codes and `api.max_requests_per_hour`
(default `50`).

### Showcase Mode

Showcase mode draws the five candidate layouts in
[docs/LayoutSpecs.md](docs/LayoutSpecs.md) with hard-coded sample data, so the
layouts can be compared in the emulator at `http://localhost:8888`. It makes no
511 requests and needs no API key.

```bash
python main.py --showcase            # cycle layouts A-E, 15 s each
python main.py --layout C            # hold one layout
python main.py --stale               # draw times in yellow, as for stale data
```

`--layout` and `--stale` each imply `--showcase` and can be combined. Rotating
layouts (A, C, D) switch lines every 5 s. A `config.yaml` copied before showcase
mode existed needs `gray: [120, 120, 120]` and `dim: [60, 60, 60]` added to
`colors`; see `config.yaml.example`.

### Assets

Pixel art is drawn in Pixelorama and stored as PNG in `assets/`. One image
pixel is one LED.

1. Draw at the exact size the art will occupy, no larger than the 128x64 panel.
2. Export as PNG at 1x scale with a transparent background.
3. Save to `assets/<name>.png`.
4. Load it with `display.image.load_image` and draw it with
   `display.render.draw_image(canvas, image, x, y)`.

Fully transparent pixels are skipped, so whatever is already on the canvas
shows through; every other pixel is drawn with its RGB value as-is.

## Running Tests

```bash
pytest
```

## Raspberry Pi Deployment

See [docs/PiSetup.md](docs/PiSetup.md) for hardware constraints, building the
`rgbmatrix` bindings, configuration, and installing the systemd unit in
`deploy/powell-muni.service`.

## Reference

- [511 SF Bay Open Data Specification - Transit](<docs/511 SF Bay Open Data Specification - Transit.pdf>)
