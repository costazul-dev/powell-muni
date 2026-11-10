"""Fetch 511 SIRI StopMonitoring responses for a single stop.

Endpoint and parameters: 511 spec section 2.10. Every call passes a stop code;
omitting it returns the whole agency and can take more than 5-7 seconds.
"""

import requests

STOP_MONITORING_URL = "https://api.511.org/transit/StopMonitoring"


def get_stop_monitoring(api_key: str, agency: str, stop_code: str, timeout: float = 10) -> bytes:
    """Return the raw response body for one stop; BOM handling lives in `transit/parse.py`.

    Raises `requests.HTTPError` on the documented 401, 404 and 500 responses.
    """
    response = requests.get(
        STOP_MONITORING_URL,
        params={"api_key": api_key, "agency": agency, "stopCode": stop_code, "format": "json"},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.content


def fetch_interval_seconds(stop_count: int, max_requests_per_hour: int) -> float:
    """Seconds between polling rounds so `stop_count` calls per round stay under the hourly cap."""
    return 3600 * stop_count / max_requests_per_hour
