from __future__ import annotations

import pytest

from fastapi_cache import FastAPICache

from backend.app.models import Dragon


@pytest.mark.asyncio
async def test_cove_uses_cached_snapshot(api_client) -> None:
    # Ensure clean cache at test start.
    if FastAPICache.get_backend():
        await FastAPICache.clear()

    d = Dragon(
        dragon_code="cove1",
        session_token="s",
        views=1,
        unique_clicks=1,
        time_remaining=10,
        is_sick=False,
    )
    await d.insert()

    res1 = await api_client.get("/api/dragons/cove")
    assert res1.status_code == 200
    payload1 = res1.json()
    assert len(payload1) == 1
    assert payload1[0]["views"] == 1

    # Change underlying data in DB; cached response should not change immediately.
    d.views = 999
    await d.save()

    res2 = await api_client.get("/api/dragons/cove")
    assert res2.status_code == 200
    payload2 = res2.json()

    assert payload2 == payload1


@pytest.mark.asyncio
async def test_geode_uses_cached_snapshot(api_client) -> None:
    # Ensure clean cache at test start.
    if FastAPICache.get_backend():
        await FastAPICache.clear()

    urgent = Dragon(
        dragon_code="geo1",
        session_token="s",
        views=0,
        unique_clicks=0,
        time_remaining=1,
        is_sick=False,
    )
    await urgent.insert()

    res1 = await api_client.get("/api/dragons/geode")
    assert res1.status_code == 200
    payload1 = res1.json()
    assert len(payload1) == 1
    assert payload1[0]["dragon_code"] == "geo1"

    urgent.views = 1234
    await urgent.save()

    res2 = await api_client.get("/api/dragons/geode")
    assert res2.status_code == 200
    payload2 = res2.json()

    assert payload2 == payload1

