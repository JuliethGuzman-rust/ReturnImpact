"""
co2_api.py
Climatiq Intermodal Freight API v3 helper.

Important:
- route must alternate:
    {"location": "..."} (optionally with location_options)
    {"transport_mode": "road|air|sea|rail"}
    {"location": "..."}
- Do NOT wrap legs in {"leg": {...}} for v3.
- In this endpoint/version, options only supports include_path (NOT automatic_routing).
"""

import os
import requests


class ClimatiqError(Exception):
    pass


API_KEY = os.getenv("CLIMATIQ_API_KEY")


def _post_to_climatiq(payload):
    if not API_KEY:
        raise ClimatiqError("CLIMATIQ_API_KEY is not set in environment variables.")

    url = "https://api.climatiq.io/freight/v3/intermodal"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

    # Uncomment for debugging:
    # print("CLIMATIQ PAYLOAD:", payload)

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=20)
    except requests.exceptions.RequestException as e:
        raise ClimatiqError(f"Network error while contacting Climatiq API: {e}")

    if not response.ok:
        raise ClimatiqError(f"Climatiq API error {response.status_code}: {response.text}")

    data = response.json()

    if isinstance(data, dict):
        if "co2e" in data:
            return float(data["co2e"])
        if "data" in data and isinstance(data["data"], dict) and "co2e" in data["data"]:
            return float(data["data"]["co2e"])

    raise ClimatiqError(f"Unexpected API response format: {data}")


def _validate_route(route):
    if not isinstance(route, list) or len(route) < 3:
        raise ClimatiqError("Route must be a list with at least: location → transport_mode → location.")

    if "location" not in route[0] or "location" not in route[-1]:
        raise ClimatiqError("Route must start and end with a location.")

    for i, step in enumerate(route):
        if not isinstance(step, dict):
            raise ClimatiqError("Each route step must be an object.")
        if i % 2 == 0:
            if "location" not in step:
                raise ClimatiqError("Route must alternate: location, transport_mode, location, ...")
            loc = (step.get("location") or "").strip()
            if not loc:
                raise ClimatiqError("Locations cannot be empty.")
        else:
            if "transport_mode" not in step:
                raise ClimatiqError("Route must alternate: location, transport_mode, location, ...")
            mode = (step.get("transport_mode") or "").strip()
            if not mode:
                raise ClimatiqError("Each leg must include a transport mode.")


def calculate_co2_intermodal_route(route, weight_kg):
    _validate_route(route)

    payload = {
        "route": route,
        "cargo": {"weight": float(weight_kg), "weight_unit": "kg"},
        # options supports include_path, so keep it empty unless you want the path
        "options": {},  # or {"include_path": True}
    }
    return _post_to_climatiq(payload)
