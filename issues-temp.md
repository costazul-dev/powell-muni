**Chore**: Scaffold repository layout, dependency files, and example config for `powell-muni`

**Context:**
- The repository contains only `511 SF Bay Open Data Specification - Transit.pdf` at the root; there is no code, config, or documentation yet.
- The project is a Python 3.11 app (the version shipped with Raspberry Pi OS Bookworm) that polls the 511 `StopMonitoring` API for three Muni lines and draws departure countdowns on a 128x64 HUB75 RGB LED matrix (Adafruit product 6484).
- Architecture is single-purpose functions grouped in `transit/` (API access and parsing) and `display/` (layout and rendering), composed by a single orchestrator `main.py`.
- Development happens on macOS using the `RGBMatrixEmulator` package; the Pi hardware backend (`rgbmatrix` from `hzeller/rpi-rgb-led-matrix`) is built from source on the Pi and is not a pip dependency.
- The 511 API key is not committed; it is read from a `.env` file. `config.yaml` and `.env` are local-only, while `config.yaml.example` and `.env.example` live in the repo.
- 511 keys are limited to 60 requests/hour by default; the fetch interval is derived from the number of distinct stops and `api.max_requests_per_hour` (default `50`) instead of being hardcoded.
- The displayed rows are lines `45` (bus, blue badge), `1` (bus, blue badge), and `T` (Muni Metro, red badge), one direction each. Direction is implied by the chosen `stop_code`, so no direction filter is needed.

**Next Steps:**

Move the spec
- [ ] `git mv "511 SF Bay Open Data Specification - Transit.pdf" "docs/511 SF Bay Open Data Specification - Transit.pdf"`

Dependency files
- [ ] Create `requirements.txt` with `requests`, `pyyaml`, `python-dotenv`
- [ ] Create `requirements-dev.txt` that starts with `-r requirements.txt` and adds `pytest`, `RGBMatrixEmulator`

Package skeleton
- [ ] Create empty `transit/__init__.py`
- [ ] Create empty `display/__init__.py`
- [ ] Create `tests/` and `tests/fixtures/` directories (with `tests/__init__.py` if needed for imports)

Example config
- [ ] Create `.env.example` containing `API_511_KEY=your-key-here`
- [ ] Create `config.yaml.example` with the following keys
  - [ ]     `api.agency: SF`
  - [ ]     `api.max_requests_per_hour: 50`
  - [ ]     `rows`: a list of three entries, each with `line`, `stop_code` (placeholder `"00000"`), `color`; values `"45"`/`blue`, `"1"`/`blue`, `"T"`/`red`
  - [ ]     `colors`: RGB triples for `blue`, `red`, `white`, `yellow`
  - [ ]     `display.backend: emulator` (allowed values `emulator`, `hardware`)
  - [ ]     `display.redraw_seconds: 15`
  - [ ]     `display.font: fonts/9x18.bdf`
  - [ ]     `display.brightness: 60`
  - [ ]     `display.hardware`: `rows: 64`, `cols: 128`, `hardware_mapping: adafruit-hat`, `gpio_slowdown: 4`

Ignore rules
- [ ] Create `.gitignore` with `.env`, `config.yaml`, `.venv/`, `__pycache__/`, `.pytest_cache/`, `emulator_config.json`

README skeleton
- [ ] Create `README.md` with sections: Overview, Repository Layout, Local Development (macOS), Running Tests, Raspberry Pi Deployment (placeholder), and a link to `docs/511 SF Bay Open Data Specification - Transit.pdf`

---

**Feature**: Add `parse_arrivals` to `transit/parse.py` with a Muni `StopMonitoring` fixture and tests

**Context:**
- `StopMonitoring` responses follow SIRI: `Siri.ServiceDelivery.StopMonitoringDelivery.MonitoredStopVisit[].MonitoredVehicleJourney` (spec section 2.10, Appendix B.1.10).
- Each visit carries `LineRef`, and `MonitoredCall` carries `ExpectedArrivalTime` and `AimedArrivalTime` as ISO 8601 strings with UTC offsets; `MonitoringRef` holds the stop code.
- The Appendix B.1.10 example is not valid JSON (`"LineRef":” Warm Springs…”` uses curly quotes), is a BART example, and shows `MonitoredStopVisit` as a single object, while the live API returns a list.
- 511 JSON responses are prefixed with a UTF-8 byte order mark, which makes `json.loads` on the raw text fail.
- No API key exists yet, so the fixture is hand-written from the Appendix B.1.10 structure and is to be replaced by a captured live response later.

**Next Steps:**

Fixture
- [ ] Create `tests/fixtures/stop_monitoring_sample.json` following the Appendix B.1.10 structure with `MonitoredStopVisit` as a list
  - [ ]     Three visits with `LineRef: "45"` and both `ExpectedArrivalTime` and `AimedArrivalTime`
  - [ ]     One visit with `LineRef: "45"` and only `AimedArrivalTime`
  - [ ]     One visit with neither arrival time
  - [ ]     One visit with a different `LineRef` (e.g. `"30"`) to confirm parsing keeps all lines (filtering happens in `display/layout.py`)
  - [ ]     `MonitoringRef` set to placeholder `"00000"`
  - [ ]     No BOM in the file itself; tests prepend it

Parser
- [ ] Create `transit/parse.py` with an `Arrival` dataclass: `line: str`, `stop_code: str`, `expected: datetime`
- [ ] Add `decode_response(raw: bytes) -> dict`: decode with `utf-8-sig` (strips the BOM) and `json.loads`
- [ ] Add `extract_visits(payload: dict) -> list[dict]`: return `MonitoredStopVisit`, wrapping a single dict in a list and returning `[]` when the key is missing
- [ ] Add `to_arrival(visit: dict) -> Arrival | None`: read `LineRef`, `MonitoringRef`, and `ExpectedArrivalTime` falling back to `AimedArrivalTime`; return `None` when both are missing; parse with `datetime.fromisoformat`
- [ ] Add `parse_arrivals(raw: bytes) -> list[Arrival]` composing the three functions above and dropping `None` results

Tests
- [ ] Create `tests/test_parse.py`
  - [ ]     `parse_arrivals` on fixture bytes prefixed with `b"\xef\xbb\xbf"` returns the expected count and values
  - [ ]     `to_arrival` falls back to `AimedArrivalTime` when `ExpectedArrivalTime` is absent
  - [ ]     `to_arrival` returns `None` when both times are absent
  - [ ]     `extract_visits` handles a single-dict `MonitoredStopVisit` and a missing key

---

**Feature**: Add `get_stop_monitoring` and `fetch_interval_seconds` to `transit/fetch.py`

**Context:**
- Endpoint: `GET https://api.511.org/transit/StopMonitoring` with parameters `api_key`, `agency`, `stopCode`, `format` (spec section 2.10).
- Muni's agency code is `SF`. Each call covers one stop and returns every line serving it.
- Omitting `stopCode` returns the whole agency and can take more than 5–7 seconds (spec section 2.10), so every call passes a stop code.
- Documented errors: `401` (invalid key), `404`, `500`.
- 511 keys are limited to 60 requests/hour by default; with 3 distinct stops and `max_requests_per_hour: 50`, the interval is `3600 * 3 / 50 = 216` seconds.

**Next Steps:**

Fetch
- [ ] Create `transit/fetch.py` with constant `STOP_MONITORING_URL = "https://api.511.org/transit/StopMonitoring"`
- [ ] Add `get_stop_monitoring(api_key: str, agency: str, stop_code: str, timeout: float = 10) -> bytes`
  - [ ]     `requests.get` with params `api_key`, `agency`, `stopCode`, `format=json`
  - [ ]     Call `response.raise_for_status()` and return `response.content` (raw bytes; BOM handling lives in `transit/parse.py`)

Interval
- [ ] Add `fetch_interval_seconds(stop_count: int, max_requests_per_hour: int) -> float` returning `3600 * stop_count / max_requests_per_hour`

Tests
- [ ] Create `tests/test_fetch.py` covering `fetch_interval_seconds(3, 50) == 216` and `fetch_interval_seconds(1, 60) == 60`

---

**Feature**: Add `build_rows` to `display/layout.py` with countdown and stale-data tests

**Context:**
- Each display row shows a route badge and up to three countdown times, e.g. `45  3, 11, 24`; destination text is omitted.
- Times are white. They turn yellow when the stop's last successful fetch is older than `2 * fetch_interval_seconds`, or when the line has no upcoming arrivals (rendered as `--`). Smarter handling (late night, outages) is out of scope.
- Countdowns are recomputed from cached `Arrival.expected` values every `display.redraw_seconds` (15), so the board counts down between API fetches.
- Layout functions are pure (take `now` as an argument) so they are testable without the clock, network, or display.

**Next Steps:**

Layout functions
- [ ] Create `display/layout.py` with a `Row` dataclass: `line: str`, `badge_color: str`, `text: str`, `text_color: str`
- [ ] Add `minutes_until(expected: datetime, now: datetime) -> int`: whole minutes, rounded down
- [ ] Add `next_minutes(arrivals: list[Arrival], line: str, now: datetime, limit: int = 3) -> list[int]`: filter by `line`, drop negative values, sort ascending, return at most `limit`
- [ ] Add `is_stale(last_success: datetime | None, now: datetime, max_age_seconds: float) -> bool`: `True` when `last_success` is `None` or older than `max_age_seconds`
- [ ] Add `format_times(minutes: list[int]) -> str`: `"3, 11, 24"`, or `"--"` when empty
- [ ] Add `build_row(row_config: dict, arrivals: list[Arrival], last_success: datetime | None, now: datetime, max_age_seconds: float) -> Row`: `text_color` is `"yellow"` when stale or when there are no minutes, otherwise `"white"`
- [ ] Add `build_rows(rows_config: list[dict], arrivals_by_stop: dict[str, list[Arrival]], last_success_by_stop: dict[str, datetime | None], now: datetime, max_age_seconds: float) -> list[Row]` mapping `build_row` over `rows_config`

Tests
- [ ] Create `tests/test_layout.py`
  - [ ]     `minutes_until` rounds down (e.g. 3m59s → `3`)
  - [ ]     `next_minutes` filters by line, drops past arrivals, sorts, and caps at `limit`
  - [ ]     `is_stale` for `None`, fresh, and expired timestamps
  - [ ]     `format_times` for populated and empty lists
  - [ ]     `build_row` returns `text_color == "white"` for fresh data, `"yellow"` for stale data, and `"yellow"` with `text == "--"` for no arrivals

---

**Feature**: Add matrix rendering with emulator and hardware backends in `display/render.py`

**Context:**
- `RGBMatrixEmulator` mirrors the `rgbmatrix` Python API (`RGBMatrix`, `RGBMatrixOptions`, `graphics`), so drawing code is identical on macOS and the Pi; only the imported module differs.
- The backend is selected explicitly via `display.backend` (`emulator` or `hardware`) in `config.yaml`, not by import auto-detection.
- `rgbmatrix` is only importable on the Pi, so imports happen inside the backend loader rather than at module top level.
- The panel is 128x64; three rows at 18px per row fit a `9x18` BDF font (`45  3, 11, 24` is 13 characters × 9px = 117px wide).
- Badges are filled rectangles in the row's `badge_color` (blue for `45` and `1`, red for `T`) with white route text; times are drawn in `Row.text_color`.
- BDF fonts ship in the `fonts/` directory of `hzeller/rpi-rgb-led-matrix`.

**Next Steps:**

Font
- [ ] Copy `fonts/9x18.bdf` from `hzeller/rpi-rgb-led-matrix` into `fonts/9x18.bdf` in this repo

Backend
- [ ] Create `display/render.py` with `load_backend(name: str)`: return the `RGBMatrixEmulator` module for `"emulator"` or the `rgbmatrix` module for `"hardware"`; raise `ValueError` otherwise
- [ ] Add `create_matrix(backend, display_config: dict)`: build `RGBMatrixOptions` from `display.hardware` (`rows`, `cols`, `hardware_mapping`, `gpio_slowdown`) and `display.brightness`; return `backend.RGBMatrix(options=options)`
- [ ] Add `load_font(backend, path: str)`: `backend.graphics.Font()` then `LoadFont(path)`

Drawing
- [ ] Add `to_color(backend, rgb: list[int])` returning `backend.graphics.Color(*rgb)`
- [ ] Add `draw_badge(canvas, backend, font, x: int, y: int, line: str, rgb: list[int])`: filled rectangle sized to the route text plus padding, with the route text in white
- [ ] Add `draw_row(canvas, backend, font, y: int, row: Row, colors: dict)`: badge at left, `row.text` after it in `colors[row.text_color]`
- [ ] Add `draw_rows(canvas, backend, font, rows: list[Row], colors: dict)`: `canvas.Clear()`, then `draw_row` per row at a vertical offset of `index * (64 // len(rows))`
- [ ] Add `show(matrix, canvas)` returning `matrix.SwapOnVSync(canvas)`

Manual check
- [ ] Run with `display.backend: emulator` on macOS and confirm three rows render with correct badge colors and that no text clips at 128px

---

**Feature**: Add `main.py` orchestrator and `config.py` loaders

**Context:**
- `main.py` is the only file that composes modules: load config → create matrix → loop { fetch stops when due → build rows → draw → sleep `display.redraw_seconds` }.
- Fetching runs on a separate, slower cadence derived from `transit.fetch.fetch_interval_seconds` (216s for 3 stops at `max_requests_per_hour: 50`); redrawing runs every 15s from cached arrivals.
- A failed fetch for a stop (network error, non-2xx, parse error) must not crash the loop; the previous arrivals for that stop are kept and `display.layout.is_stale` turns its times yellow once they age out.
- The API key is read from `API_511_KEY` in `.env` via `python-dotenv`.
- Output goes to stdout through `logging`, which `journalctl` collects when run under systemd.

**Next Steps:**

Config loading
- [ ] Create `config.py` with `load_config(path: str) -> dict` using `yaml.safe_load`
- [ ] Add `load_api_key() -> str`: call `dotenv.load_dotenv()`, read `API_511_KEY`, raise `RuntimeError` with a clear message when it is missing

Orchestrator helpers in `main.py`
- [ ] Add `unique_stops(rows_config: list[dict]) -> list[str]`: distinct `stop_code` values in order
- [ ] Add `refresh_stop(api_key, agency, stop_code) -> list[Arrival]`: `get_stop_monitoring` then `parse_arrivals`
- [ ] Add `refresh_all(api_key, agency, stops, arrivals_by_stop, last_success_by_stop, now)`: call `refresh_stop` per stop inside `try`/`except Exception`; on success update both dicts, on failure log the exception and leave the previous values

Main loop
- [ ] Add `main()`
  - [ ]     Parse `--config` with `argparse` (default `config.yaml`)
  - [ ]     Load config and API key, compute `interval = fetch_interval_seconds(len(stops), config["api"]["max_requests_per_hour"])` and `max_age_seconds = 2 * interval`
  - [ ]     `backend = load_backend(config["display"]["backend"])`, `matrix = create_matrix(...)`, `canvas = matrix.CreateFrameCanvas()`, `font = load_font(...)`
  - [ ]     Loop: when `now >= next_fetch_at`, call `refresh_all` and set `next_fetch_at = now + interval`; `build_rows`; `draw_rows`; `canvas = show(matrix, canvas)`; `time.sleep(config["display"]["redraw_seconds"])`
  - [ ]     Use timezone-aware `datetime.now(timezone.utc)` for `now`
- [ ] Add `if __name__ == "__main__": main()`

Docs
- [ ] Fill in the Local Development section of `README.md`: create venv, `pip install -r requirements-dev.txt`, copy `config.yaml.example` → `config.yaml` and `.env.example` → `.env`, run `python main.py`, run `pytest`

---

**Chore**: Add systemd unit `deploy/powell-muni.service` and `docs/PiSetup.md`

**Context:**
- On the Pi, `main.py` runs as one long-lived process. A systemd timer is not used because the matrix library refreshes the panel from a background thread and the panel goes dark when the process exits.
- `rgbmatrix` needs root to access GPIO and drops privileges after initialization, so the unit runs as root.
- `rpi-rgb-led-matrix` does not support the Raspberry Pi 5; supported targets include the Pi 4, Pi 3B+, and Pi Zero 2 W. The Pi model and the controller board (Adafruit RGB Matrix Bonnet or HAT) are not yet chosen and are decided after the emulator build is complete.
- Adafruit 6484 is a 1/32-scan panel that uses 5 address lines (requires the `E` line) and can draw up to 4A at 5V, so it needs a dedicated 5V/4A supply.
- The `rgbmatrix` Python bindings are built from source per `hzeller/rpi-rgb-led-matrix` `bindings/python/README.md` and are not in `requirements.txt`.

**Next Steps:**

systemd unit
- [ ] Create `deploy/powell-muni.service`
  - [ ]     `[Unit]`: `Description=powell-muni transit display`, `Wants=network-online.target`, `After=network-online.target`
  - [ ]     `[Service]`: `Type=simple`, `User=root`, `WorkingDirectory=/opt/powell-muni`, `ExecStart=/opt/powell-muni/.venv/bin/python main.py --config /opt/powell-muni/config.yaml`, `Restart=always`, `RestartSec=10`
  - [ ]     `[Install]`: `WantedBy=multi-user.target`

Pi setup guide
- [ ] Create `docs/PiSetup.md`
  - [ ]     Hardware constraints: no Pi 5; 5V/4A dedicated supply; `E` address line required (link the Adafruit 6484 page and the Bonnet/HAT guide for jumper setup)
  - [ ]     Clone the repo to `/opt/powell-muni` and create `.venv` with `python3 -m venv --system-site-packages .venv`
  - [ ]     Install `requirements.txt` (not `requirements-dev.txt`)
  - [ ]     Build and install the `rgbmatrix` Python bindings following upstream `bindings/python/README.md`
  - [ ]     Disable onboard audio (`dtparam=audio=off`), which conflicts with the matrix timing
  - [ ]     Set `display.backend: hardware` in `config.yaml` and tune `display.hardware.gpio_slowdown` for the chosen Pi model
  - [ ]     Install the unit: copy to `/etc/systemd/system/`, `systemctl daemon-reload`, `systemctl enable --now powell-muni`, view logs with `journalctl -u powell-muni -f`

README
- [ ] Replace the Raspberry Pi Deployment placeholder in `README.md` with a link to `docs/PiSetup.md`
