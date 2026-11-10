from datetime import datetime, timedelta, timezone
from pathlib import Path

from transit.parse import Arrival, extract_visits, parse_arrivals, to_arrival

FIXTURE = Path(__file__).parent / "fixtures" / "stop_monitoring_sample.json"
BOM = b"\xef\xbb\xbf"
PST = timezone(timedelta(hours=-8))


def _visit(**call):
    return {
        "MonitoringRef": "00000",
        "MonitoredVehicleJourney": {"LineRef": "45", "MonitoredCall": call},
    }


def test_parse_arrivals_from_bom_prefixed_fixture():
    arrivals = parse_arrivals(BOM + FIXTURE.read_bytes())

    assert len(arrivals) == 5
    assert [a.line for a in arrivals] == ["45", "45", "45", "45", "30"]
    assert all(a.stop_code == "00000" for a in arrivals)
    assert arrivals[0] == Arrival("45", "00000", datetime(2026, 11, 9, 10, 5, 12, tzinfo=PST))
    assert arrivals[3].expected == datetime(2026, 11, 9, 10, 34, tzinfo=PST)
    assert arrivals[4] == Arrival("30", "00000", datetime(2026, 11, 9, 10, 8, 30, tzinfo=PST))


def test_to_arrival_falls_back_to_aimed_time():
    arrival = to_arrival(_visit(AimedArrivalTime="2026-11-09T10:34:00-08:00"))

    assert arrival is not None
    assert arrival.expected == datetime(2026, 11, 9, 10, 34, tzinfo=PST)


def test_to_arrival_returns_none_without_times():
    assert to_arrival(_visit()) is None


def test_extract_visits_wraps_single_dict():
    visit = _visit(AimedArrivalTime="2026-11-09T10:34:00-08:00")
    payload = {"Siri": {"ServiceDelivery": {"StopMonitoringDelivery": {"MonitoredStopVisit": visit}}}}

    assert extract_visits(payload) == [visit]


def test_extract_visits_missing_key_returns_empty():
    payload = {"Siri": {"ServiceDelivery": {"StopMonitoringDelivery": {}}}}

    assert extract_visits(payload) == []
