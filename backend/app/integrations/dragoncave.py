from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx

from backend.app.core import get_settings


BASE_URL = "https://dragcave.net/api/v2/"
DEFAULT_TIMEOUT_S = 15.0
SICK_THRESHOLD_HOURS = 24


@dataclass(frozen=True)
class CrystalStats:
    dragon_code: str
    views: int
    unique_clicks: int
    time_remaining: int
    is_sick: bool


class DragonCaveAPIError(RuntimeError):
    pass


def load_httpx_json_object(resp: httpx.Response, context: str) -> dict[str, Any]:
    """
    Parse a Dragon Cave JSON body. Raises DragonCaveAPIError on HTML, empty bodies,
    or invalid JSON (common when the key is wrong or the endpoint returns an error page).
    """
    text = (resp.text or "").strip()
    ct = (resp.headers.get("content-type") or "").lower()
    if not text:
        raise DragonCaveAPIError(f"{context}: empty response body (HTTP {resp.status_code}).")
    if "application/json" not in ct and not text.startswith("{"):
        raise DragonCaveAPIError(
            f"{context}: expected JSON, got content-type {ct!r}; body starts: {text[:280]!r}"
        )
    try:
        val = json.loads(text)
    except json.JSONDecodeError as e:
        raise DragonCaveAPIError(
            f"{context}: invalid JSON (HTTP {resp.status_code}); body starts: {text[:280]!r}"
        ) from e
    if not isinstance(val, dict):
        raise DragonCaveAPIError(f"{context}: expected JSON object, got {type(val).__name__}")
    return val


def _auth_headers() -> dict[str, str]:
    settings = get_settings()
    if not settings.dc_api_key:
        raise DragonCaveAPIError("Missing DC_API_KEY environment variable.")
    return {"Authorization": f"Bearer {settings.dc_api_key}"}


def _parse_error_array(payload: dict[str, Any]) -> None:
    errors = payload.get("errors") or []
    if not isinstance(errors, list):
        raise DragonCaveAPIError("Invalid API response: `errors` is not a list.")

    hard_errors: list[str] = []
    for entry in errors:
        if not (isinstance(entry, (list, tuple)) and len(entry) == 2):
            continue
        code, message = entry
        if code == 0:
            continue
        hard_errors.append(f"{code}: {message}")

    if hard_errors:
        raise DragonCaveAPIError("Dragon Cave API error(s): " + "; ".join(hard_errors))


def _as_int(payload: dict[str, Any], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, bool) or value is None:
        raise DragonCaveAPIError(f"Invalid API response: `{key}` missing or not an int.")
    try:
        return int(value)
    except Exception as e:
        raise DragonCaveAPIError(f"Invalid API response: `{key}` not an int-like value.") from e


async def fetch_crystal_stats(dragon_code: str) -> CrystalStats:
    """
    Fetch a single egg/hatchling/dragon record from Dragon Cave and map it to
    our minimal persisted fields.

    Uses: GET /dragon/{id}
    Docs: https://dragcave.net/api/docs
    """

    url = f"{BASE_URL}dragon/{dragon_code}"
    timeout = httpx.Timeout(DEFAULT_TIMEOUT_S)

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(url, headers=_auth_headers())

    if resp.status_code != 200:
        raise DragonCaveAPIError(f"Dragon Cave API HTTP {resp.status_code}: {resp.text[:500]}")

    payload = load_httpx_json_object(resp, f"Dragon Cave v2 GET /dragon/{dragon_code}")
    _parse_error_array(payload)

    views = _as_int(payload, "views")
    unique_clicks = _as_int(payload, "unique")
    time_remaining = _as_int(payload, "hoursleft")

    is_sick = time_remaining >= 0 and time_remaining <= SICK_THRESHOLD_HOURS

    return CrystalStats(
        dragon_code=dragon_code,
        views=views,
        unique_clicks=unique_clicks,
        time_remaining=time_remaining,
        is_sick=is_sick,
    )

