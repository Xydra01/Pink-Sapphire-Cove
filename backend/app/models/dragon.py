from __future__ import annotations

from datetime import datetime

from beanie import Document, Indexed
from pydantic import Field


class Dragon(Document):
    """
    Minimal dragon record.

    This intentionally stores no user-identifying information. Ownership is
    tracked by `session_token` which is a temporary capability token.
    """

    dragon_code: Indexed(str, unique=True)
    session_token: Indexed(str)

    views: int = 0
    unique_clicks: int = 0

    # Hours until death for eggs/hatchlings. (Dragon Cave API: hoursleft)
    # -1 hidden/frozen/adult, -2 dead.
    time_remaining: int = Field(default=-1)

    is_sick: bool = False

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "dragons"

