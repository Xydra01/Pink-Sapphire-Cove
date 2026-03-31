"""
Dragon Cave legacy JSON API (key in URL path).

Used for scroll-style actions such as ``user_young`` that are not covered by the
v2 bearer endpoints we use for per-dragon stats. Docs (deprecated but supported):
https://dragcave.net/api.txt
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote, unquote

import httpx

from backend.app.core import get_settings

from .dragoncave import (
    CrystalStats,
    DragonCaveAPIError,
    SICK_THRESHOLD_HOURS,
    _as_int,
    load_httpx_json_object,
)

DEFAULT_TIMEOUT_S = 20.0

# Public scroll profile URL: https://dragcave.net/user/{name}
SCROLL_USER_RE = re.compile(r"dragcave\.net/user/([^/?#]+)", re.IGNORECASE)

# After extracting from URL, disallow characters that would break requests or look wrong.
_SAFE_USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{1,80}$")


def parse_scroll_username(raw: str) -> str:
    """
    Accept a bare Dragon Cave username or a full scroll/profile URL and return the username.
    """
    s = (raw or "").strip().lstrip("@")
    if not s:
        raise ValueError("Scroll input is empty.")

    m = SCROLL_USER_RE.search(s)
    if m:
        s = unquote(m.group(1))

    if not _SAFE_USERNAME_RE.match(s):
        raise ValueError(
            "Could not read a valid Dragon Cave username. Paste your scroll link "
            "(dragcave.net/user/…) or type your username."
        )
    return s


def _parse_legacy_errors(payload: dict[str, Any]) -> None:
    errors = payload.get("errors") or []
    if not isinstance(errors, list):
        raise DragonCaveAPIError("Invalid legacy API response: `errors` is not a list.")

    hard: list[str] = []
    for entry in errors:
        if not (isinstance(entry, (list, tuple)) and len(entry) == 2):
            continue
        code, message = entry
        if code == 0:
            continue
        hard.append(f"{code}: {message}")

    if hard:
        raise DragonCaveAPIError("Dragon Cave legacy API: " + "; ".join(hard))


async def fetch_crystal_stats_legacy(dragon_code: str) -> CrystalStats:
    """
    Legacy ``/api/{key}/json/view/{id}`` (see api.txt). Same ``DC_API_KEY`` as
    ``user_young``; used when v2 ``Bearer`` returns 401 Invalid API key for that key.
    """
    settings = get_settings()
    if not settings.dc_api_key:
        raise DragonCaveAPIError("Missing DC_API_KEY environment variable.")

    key = settings.dc_api_key.strip()
    code = (dragon_code or "").strip()
    if not code:
        raise DragonCaveAPIError("Dragon code is empty.")

    url = f"https://dragcave.net/api/{key}/json/view/{code}"
    timeout = httpx.Timeout(DEFAULT_TIMEOUT_S)

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url)
    except httpx.HTTPError as e:
        tail = str(e).strip() or type(e).__name__
        raise DragonCaveAPIError(f"Dragon Cave legacy view network error: {tail}") from e

    if resp.status_code != 200:
        loc = (resp.headers.get("location") or "").strip()
        hint = f" (Location: {loc})" if loc and 300 <= resp.status_code < 400 else ""
        raise DragonCaveAPIError(
            f"Dragon Cave legacy view HTTP {resp.status_code}{hint}: {resp.text[:500]}"
        )

    payload = load_httpx_json_object(resp, f"Dragon Cave legacy view/{code}")
    _parse_legacy_errors(payload)

    raw = payload.get("dragons")
    if raw is None:
        raise DragonCaveAPIError("Legacy view: missing `dragons`.")
    if isinstance(raw, dict):
        rows = [v for v in raw.values() if isinstance(v, dict)]
    elif isinstance(raw, list):
        rows = [r for r in raw if isinstance(r, dict)]
    else:
        raise DragonCaveAPIError("Legacy view: `dragons` has unexpected type.")

    if not rows:
        raise DragonCaveAPIError("Dragon Cave legacy view: dragon not found or empty.")

    row = rows[0]
    rid = row.get("id")
    if rid is None:
        raise DragonCaveAPIError("Legacy view: missing dragon `id`.")
    out_code = str(rid).strip()
    views = _as_int(row, "views")
    unique_clicks = _as_int(row, "unique")
    time_remaining = _as_int(row, "hoursleft")
    is_sick = time_remaining >= 0 and time_remaining <= SICK_THRESHOLD_HOURS

    return CrystalStats(
        dragon_code=out_code,
        views=views,
        unique_clicks=unique_clicks,
        time_remaining=time_remaining,
        is_sick=is_sick,
    )


def _truthy_accept_aid(raw: Any) -> bool:
    if raw is True or raw == 1:
        return True
    if raw is False or raw == 0:
        return False
    if isinstance(raw, str):
        return raw.strip().lower() in ("1", "true", "yes", "on")
    return bool(raw)


async def fetch_user_young_scroll(username: str) -> list[dict[str, Any]]:
    """
    Call ``user_young`` for a username.

    We return ``accept_aid`` as informational only. Many hatcheries still accept eggs/hatchlings
    with Accept Aid off (it's relevant to interaction expectations, not whether a code is valid).
    """
    settings = get_settings()
    if not settings.dc_api_key:
        raise DragonCaveAPIError("Missing DC_API_KEY environment variable.")

    # Legacy docs: https://dragcave.net/api/{private_key}/json/{action}?...
    # The key is inserted verbatim into the path (Dragon Cave expects the raw private key here).
    key = settings.dc_api_key.strip()
    user_q = quote(username, safe="")
    url = f"https://dragcave.net/api/{key}/json/user_young?username={user_q}"
    timeout = httpx.Timeout(DEFAULT_TIMEOUT_S)

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url)
    except httpx.HTTPError as e:
        # httpx timeouts often stringify to "" — include the exception class name.
        tail = str(e).strip() or type(e).__name__
        raise DragonCaveAPIError(f"Dragon Cave legacy API network error: {tail}") from e

    if resp.status_code != 200:
        loc = (resp.headers.get("location") or "").strip()
        hint = f" (Location: {loc})" if loc and 300 <= resp.status_code < 400 else ""
        raise DragonCaveAPIError(
            f"Dragon Cave legacy API HTTP {resp.status_code}{hint}: {resp.text[:500]}"
        )

    payload = load_httpx_json_object(resp, "Dragon Cave legacy user_young")

    _parse_legacy_errors(payload)

    dragons = payload.get("dragons")
    if dragons is None:
        return []
    if isinstance(dragons, dict):
        dragons = [v for v in dragons.values() if isinstance(v, dict)]
    elif not isinstance(dragons, list):
        raise DragonCaveAPIError("Invalid legacy API response: `dragons` is not a list or object.")

    out: list[dict[str, Any]] = []
    for row in dragons:
        if not isinstance(row, dict):
            continue
        code = row.get("id")
        if code is None:
            continue
        dragon_code = str(code).strip()
        if not dragon_code:
            continue
        name = row.get("name")
        name_str = str(name).strip() if name is not None else ""
        out.append(
            {
                "dragon_code": dragon_code,
                "name": name_str,
                "accept_aid": _truthy_accept_aid(row.get("acceptaid")),
            }
        )
    return out
