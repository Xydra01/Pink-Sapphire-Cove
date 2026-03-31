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

from .dragoncave import DragonCaveAPIError

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
    Call ``user_young`` for a username. Returns dicts with dragon_code, name, can_add
    (Accept Aid enabled — required for third-party hatchery interaction per DC API docs).
    """
    settings = get_settings()
    if not settings.dc_api_key:
        raise DragonCaveAPIError("Missing DC_API_KEY environment variable.")

    key = quote(settings.dc_api_key, safe="")
    user_q = quote(username, safe="")
    url = f"https://dragcave.net/api/{key}/json/user_young?username={user_q}"
    timeout = httpx.Timeout(DEFAULT_TIMEOUT_S)

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(url)

    if resp.status_code != 200:
        raise DragonCaveAPIError(f"Dragon Cave legacy API HTTP {resp.status_code}: {resp.text[:500]}")

    payload = resp.json()
    if not isinstance(payload, dict):
        raise DragonCaveAPIError("Invalid legacy API response: expected JSON object.")

    _parse_legacy_errors(payload)

    dragons = payload.get("dragons")
    if dragons is None:
        return []
    if not isinstance(dragons, list):
        raise DragonCaveAPIError("Invalid legacy API response: `dragons` is not a list.")

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
                "can_add": _truthy_accept_aid(row.get("acceptaid")),
            }
        )
    return out
