from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    dc_api_key: str | None


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

    load_dotenv(override=False)


def get_settings() -> Settings:
    _maybe_load_dotenv()
    return Settings(dc_api_key=os.getenv("DC_API_KEY"))

