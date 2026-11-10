"""Orchestrator: load config, fetch arrivals on the polling interval, redraw rows from the cache.

Fetching and drawing run on separate cadences. Each stop is fetched every
`fetch_interval_seconds` to stay under the 511 hourly cap; rows are redrawn every
`display.redraw_seconds` from cached arrivals so countdowns keep ticking between fetches.
"""

import argparse
import logging
import sys
import time
from datetime import datetime, timedelta, timezone

from config import load_api_key, load_config
from display.layout import build_rows
from display.render import create_matrix, draw_rows, load_backend, load_font, show
from transit.fetch import fetch_interval_seconds, get_stop_monitoring
from transit.parse import Arrival, parse_arrivals

logger = logging.getLogger("powell_muni")


def unique_stops(rows_config: list[dict]) -> list[str]:
    """Distinct `stop_code` values in the order rows list them."""
    return list(dict.fromkeys(row["stop_code"] for row in rows_config))


def refresh_stop(api_key: str, agency: str, stop_code: str) -> list[Arrival]:
    """Fetch and parse current arrivals for one stop."""
    return parse_arrivals(get_stop_monitoring(api_key, agency, stop_code))


def refresh_all(
    api_key: str,
    agency: str,
    stops: list[str],
    arrivals_by_stop: dict[str, list[Arrival]],
    last_success_by_stop: dict[str, datetime | None],
    now: datetime,
) -> None:
    """Refresh every stop in place; a failed stop is logged and keeps its previous arrivals."""
    for stop_code in stops:
        try:
            arrivals = refresh_stop(api_key, agency, stop_code)
        except Exception:
            logger.exception("fetch failed for stop %s; keeping previous arrivals", stop_code)
            continue
        arrivals_by_stop[stop_code] = arrivals
        last_success_by_stop[stop_code] = now
        logger.info("fetched %d arrivals for stop %s", len(arrivals), stop_code)


def main() -> None:
    parser = argparse.ArgumentParser(description="Muni departure board for an RGB LED matrix")
    parser.add_argument("--config", default="config.yaml", help="path to the YAML config (default: config.yaml)")
    args = parser.parse_args()

    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    config = load_config(args.config)
    api_key = load_api_key()
    agency = config["api"]["agency"]
    rows_config = config["rows"]
    display_config = config["display"]
    colors = config["colors"]

    stops = unique_stops(rows_config)
    interval = fetch_interval_seconds(len(stops), config["api"]["max_requests_per_hour"])
    max_age_seconds = 2 * interval
    logger.info("polling %d stops every %.0fs", len(stops), interval)

    backend = load_backend(display_config["backend"])
    matrix = create_matrix(backend, display_config)
    canvas = matrix.CreateFrameCanvas()
    font = load_font(backend, display_config["font"])

    arrivals_by_stop: dict[str, list[Arrival]] = {}
    last_success_by_stop: dict[str, datetime | None] = {}
    next_fetch_at: datetime | None = None

    while True:
        now = datetime.now(timezone.utc)
        if next_fetch_at is None or now >= next_fetch_at:
            refresh_all(api_key, agency, stops, arrivals_by_stop, last_success_by_stop, now)
            next_fetch_at = now + timedelta(seconds=interval)
        rows = build_rows(rows_config, arrivals_by_stop, last_success_by_stop, now, max_age_seconds)
        draw_rows(canvas, backend, font, rows, colors)
        canvas = show(matrix, canvas)
        time.sleep(display_config["redraw_seconds"])


if __name__ == "__main__":
    main()
