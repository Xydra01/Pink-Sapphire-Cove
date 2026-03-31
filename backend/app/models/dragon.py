from __future__ import annotations

from datetime import datetime

from beanie import Document, Indexed, Insert, Replace, Save, before_event
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

    # Phase 2: persisted urgency metadata for the Geode.
    urgency_score: float = 0.0
    is_urgent: bool = False

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "dragons"

    @staticmethod
    def _compute_urgency_score(views: int, time_remaining: int) -> tuple[float, bool]:
        """
        Compute urgency based on remaining required views and time left.

        - Uses a fixed VIEWS_NEEDED constant derived from community guidance.
        - Only eggs/hatchlings with 0 <= time_remaining <= 48 can be urgent.
        """

        VIEWS_NEEDED = 12_000

        # Only consider living, growing dragons within a 48-hour window.
        if time_remaining < 0 or time_remaining > 48:
            return 0.0, False

        remaining_required_views = max(0, VIEWS_NEEDED - max(0, views))

        # Avoid division by zero when time_remaining is 0.
        denom = float(time_remaining) if time_remaining > 0 else 1.0
        score = remaining_required_views / denom if remaining_required_views > 0 else 0.0

        is_urgent = score >= 1.0
        return score, is_urgent

    @before_event(Insert, Save, Replace)
    def _update_urgency_fields(self) -> None:
        score, urgent = self._compute_urgency_score(self.views, self.time_remaining)
        self.urgency_score = score
        self.is_urgent = urgent

