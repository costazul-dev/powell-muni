from transit.fetch import fetch_interval_seconds


def test_fetch_interval_for_three_stops_at_fifty_per_hour():
    assert fetch_interval_seconds(3, 50) == 216


def test_fetch_interval_for_one_stop_at_sixty_per_hour():
    assert fetch_interval_seconds(1, 60) == 60
