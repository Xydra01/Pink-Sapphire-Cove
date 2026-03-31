from __future__ import annotations

from dataclasses import dataclass

import pytest

import backend.app.sweeper as sweeper
from backend.app.models import Dragon


@dataclass(frozen=True)
class _FakeStats:
    dragon_code: str
    views: int
    unique_clicks: int
    time_remaining: int
    is_sick: bool


@pytest.mark.asyncio
async def test_sweeper_updates_growing_and_deletes_dead_and_adult(monkeypatch: pytest.MonkeyPatch, beanie_initialized: None) -> None:
    # Growing dragon that should be updated.
    growing = Dragon(
        dragon_code="grow",
        session_token="s",
        views=1,
        unique_clicks=1,
        time_remaining=20,
        is_sick=False,
    )
    await growing.insert()

    # Dead dragon candidate.
    dead = Dragon(
        dragon_code="dead",
        session_token="s",
        views=5,
        unique_clicks=2,
        time_remaining=5,
        is_sick=False,
    )
    await dead.insert()

    # Adult / finished dragon candidate.
    adult = Dragon(
        dragon_code="adult",
        session_token="s",
        views=10,
        unique_clicks=3,
        time_remaining=10,
        is_sick=False,
    )
    await adult.insert()

    async def fake_fetch(code: str) -> _FakeStats:
        if code == "grow":
            return _FakeStats(dragon_code=code, views=100, unique_clicks=50, time_remaining=10, is_sick=False)
        if code == "dead":
            return _FakeStats(dragon_code=code, views=200, unique_clicks=80, time_remaining=-2, is_sick=False)
        if code == "adult":
            return _FakeStats(dragon_code=code, views=300, unique_clicks=120, time_remaining=-1, is_sick=False)
        raise AssertionError(f"Unexpected code {code}")

    monkeypatch.setattr(sweeper, "fetch_crystal_stats", fake_fetch)

    await sweeper.sweep_dragons_once()

    remaining = await Dragon.find_all().to_list()
    codes = {d.dragon_code for d in remaining}

    assert "grow" in codes
    assert "dead" not in codes
    assert "adult" not in codes

    stored_grow = next(d for d in remaining if d.dragon_code == "grow")
    assert stored_grow.views == 100
    assert stored_grow.unique_clicks == 50
    assert stored_grow.time_remaining == 10

