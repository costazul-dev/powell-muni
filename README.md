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
tests/                   pytest suite
tests/fixtures/          Recorded API responses used by tests
docs/                    Reference material (511 API specification, Pi setup)
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
