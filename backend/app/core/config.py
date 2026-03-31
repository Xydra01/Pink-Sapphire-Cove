from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    dc_api_key: str | None
    dc_authorization: str | None
    mongodb_uri: str | None
    mongodb_db: str | None


def _find_repo_dotenv() -> Path | None:
    """
    Locate `.env` next to the project root (directory that contains `backend/`).

    `load_dotenv()` with no path only reads from the process cwd, so starting
    uvicorn from `backend/`, an IDE, or another folder silently skips `.env` and
    `DC_API_KEY` never loads — Dragon Cave is never called.
    """
    here = Path(__file__).resolve().parent
    for _ in range(10):
        candidate = here / ".env"
        if candidate.is_file():
            return candidate
        if here.parent == here:
            break
        here = here.parent
    return None


def _maybe_load_dotenv() -> None:
    """
    Optional local dev support.

    `python-dotenv` is intentionally optional at runtime; production should set
    environment variables via the host.
    """

    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:
        return

    path = _find_repo_dotenv()
    # In pytest, conftest sets PSC_DOTENV_OVERRIDE=0 so monkeypatched env wins.
    # Locally, default True so edits to `.env` replace stale shell exports.
    override = os.getenv("PSC_DOTENV_OVERRIDE", "1").lower() in ("1", "true", "yes")
    if path is not None:
        load_dotenv(path, override=override)
    else:
        load_dotenv(override=override)


def _env_trimmed(name: str) -> str | None:
    raw = os.getenv(name)
    if raw is None:
        return None
    t = raw.strip()
    if len(t) >= 2 and t[0] == t[-1] and t[0] in "\"'":
        t = t[1:-1].strip()
    return t if t else None


def _normalize_dc_api_key(key: str | None) -> str | None:
    """Strip a leading ``Bearer `` prefix so legacy path and default v2 header stay clean."""
    if key is None:
        return None
    t = key.strip()
    if not t:
        return None
    low = t.lower()
    if low.startswith("bearer "):
        t = t[7:].strip()
    return t if t else None


def _normalize_dc_authorization(raw: str | None) -> str | None:
    """
    Optional v2-only override: value becomes the full ``Authorization`` header.
    Accepts ``Bearer <token>`` or bare token (we prepend ``Bearer ``).
    """
    if raw is None:
        return None
    t = raw.strip()
    if len(t) >= 2 and t[0] == t[-1] and t[0] in "\"'":
        t = t[1:-1].strip()
    if not t:
        return None
    low = t.lower()
    if low.startswith("bearer "):
        return f"Bearer {t[7:].strip()}" if t[7:].strip() else None
    return f"Bearer {t}"


def get_settings() -> Settings:
    _maybe_load_dotenv()
    return Settings(
        dc_api_key=_normalize_dc_api_key(_env_trimmed("DC_API_KEY")),
        dc_authorization=_normalize_dc_authorization(_env_trimmed("DC_AUTHORIZATION")),
        mongodb_uri=_env_trimmed("MONGODB_URI"),
        mongodb_db=_env_trimmed("MONGODB_DB"),
    )


