from __future__ import annotations

from datetime import datetime, timedelta

from beanie import Document, Indexed
from pydantic import Field


class UserSession(Document):
    """
    Temporary session (capability token).

    Stores no personal information. A session token is used to authorize
    removal/management of dragons created under that session.
    """

    token: Indexed(str, unique=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(days=7))

    class Settings:
        name = "user_sessions"

