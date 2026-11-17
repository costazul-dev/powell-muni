"""Hard-coded sample data and timing for comparing the candidate layouts on the panel.

The layouts in `docs/LayoutSpecs.md` need 511 fields that `Arrival` does not carry yet,
so showcase mode draws these sample cards, which match the reference frames in
`tests/fixtures/layouts/`, and makes no API requests.
"""

from dataclasses import dataclass

LAYOUT_SECONDS = 15
LINE_SECONDS = 5
TICK_SECONDS = 0.25


@dataclass(frozen=True)
class Card:
    """One line's content as the layouts show it; `color` is a key into `colors`."""

    line: str
    color: str
    mode: str
    route_name: str
    direction: str
    stop_name: str
    destination: str
    minutes: tuple[int, ...]


SAMPLE_CARDS = (
    Card("45", "blue", "bus", "Union-Stockton", "Inbound", "Stockton St", "Caltrain Depot", (2, 10, 23)),
    Card("1", "blue", "bus", "California", "Outbound", "Sacramento St", "Geary + 33rd Av", (6, 19)),
    Card("T", "red", "rail", "Third Street", "Northbound", "Union Square", "Chinatown", (4, 17, 30)),
)

LAYOUTS = ("A", "B", "C", "D", "E")


def showcase_frame(elapsed: float, layout_seconds: float, line_seconds: float, pinned: str | None) -> tuple[str, int]:
    """The layout key and active card index to draw `elapsed` seconds into the showcase."""
    layout = pinned or LAYOUTS[int(elapsed // layout_seconds) % len(LAYOUTS)]
    active = int(elapsed // line_seconds) % len(SAMPLE_CARDS)
    return layout, active
