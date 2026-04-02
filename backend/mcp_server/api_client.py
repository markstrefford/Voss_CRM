"""HTTP client for the VOSS CRM API."""

import json
import os
import urllib.request
import urllib.error
import urllib.parse


def _get_config():
    api_url = os.environ.get("VOSS_API_URL", "http://localhost:8000")
    api_key = os.environ.get("VOSS_API_KEY", "")
    return api_url.rstrip("/"), api_key


def api_get(path: str, params: dict | None = None) -> dict | list:
    """Make a GET request to the VOSS API."""
    base_url, api_key = _get_config()
    url = f"{base_url}{path}"
    if params:
        filtered = {k: v for k, v in params.items() if v is not None and v != ""}
        if filtered:
            url += "?" + urllib.parse.urlencode(filtered)

    req = urllib.request.Request(url)
    req.add_header("X-API-Key", api_key)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"API error {e.code}: {body}") from e


def api_post(path: str, data: dict) -> dict:
    """Make a POST request to the VOSS API."""
    base_url, api_key = _get_config()
    url = f"{base_url}{path}"

    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-API-Key", api_key)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"API error {e.code}: {body}") from e


def api_put(path: str, data: dict) -> dict:
    """Make a PUT request to the VOSS API."""
    base_url, api_key = _get_config()
    url = f"{base_url}{path}"

    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, method="PUT")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-API-Key", api_key)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"API error {e.code}: {body}") from e
