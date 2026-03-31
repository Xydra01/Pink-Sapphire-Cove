from __future__ import annotations

from dataclasses import dataclass

import pytest

import backend.app.api.dragons as dragons_api
from backend.app.models import Dragon


@dataclass(frozen=True)
class _FakeStats:
    views: int
    unique_clicks: int
    time_remaining: int
    is_sick: bool


@pytest.mark.asyncio
async def test_add_dragons_creates_session_and_inserts(monkeypatch: pytest.MonkeyPatch, api_client) -> None:
    async def fake_fetch(code: str) -> _FakeStats:  # noqa: ARG001
        return _FakeStats(views=10, unique_clicks=2, time_remaining=12, is_sick=True)

    monkeypatch.setattr(dragons_api, "fetch_crystal_stats", fake_fetch)

    res = await api_client.post("/api/dragons/add", json={"dragon_codes": ["abCd3", "DeFgh"]})
    assert res.status_code == 200
    payload = res.json()
    assert "session_token" in payload and payload["session_token"]
    assert len(payload["dragons"]) == 2
    assert payload["errors"] == []

    stored = await Dragon.find().to_list()
    assert {d.dragon_code for d in stored} == {"abCd3", "DeFgh"}


@pytest.mark.asyncio
async def test_add_dragons_rejects_all_invalid(api_client) -> None:
    res = await api_client.post("/api/dragons/add", json={"dragon_codes": ["", "!!!!!!", "toolonggg"]})
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_cove_filters_sick_and_dead(api_client) -> None:
    await Dragon(
        dragon_code="a",
        session_token="s",
        views=1,
        unique_clicks=1,
        time_remaining=10,
        is_sick=False,
    ).insert()
    await Dragon(
        dragon_code="b",
        session_token="s",
        views=1,
        unique_clicks=1,
        time_remaining=10,
        is_sick=True,
    ).insert()
    await Dragon(
        dragon_code="c",
        session_token="s",
        views=1,
        unique_clicks=1,
        time_remaining=-2,
        is_sick=False,
    ).insert()

    res = await api_client.get("/api/dragons/cove")
    assert res.status_code == 200
    codes = {d["dragon_code"] for d in res.json()}
    assert codes == {"a"}


@pytest.mark.asyncio
async def test_geode_returns_urgent_sorted(api_client) -> None:
    await Dragon(
        dragon_code="soon",
        session_token="s",
        views=0,
        unique_clicks=0,
        time_remaining=1,
        is_sick=True,
    ).insert()
    await Dragon(
        dragon_code="later",
        session_token="s",
        # Extremely high views should make this non-urgent under the Phase 2 formula.
        views=200_000,
        unique_clicks=50_000,
        time_remaining=40,
        is_sick=False,
    ).insert()

    res = await api_client.get("/api/dragons/geode")
    assert res.status_code == 200
    out = res.json()
    codes = [d["dragon_code"] for d in out]
    # Only the truly urgent dragon should be returned, and it should come first.
    assert codes[0] == "soon"
    assert "later" not in codes


@pytest.mark.asyncio
async def test_geode_sorts_by_time_remaining_then_urgency(api_client) -> None:
    # Both of these should be urgent, but with different time_remaining values.
    await Dragon(
        dragon_code="sooner",
        session_token="s",
        views=0,
        unique_clicks=0,
        time_remaining=2,
        is_sick=False,
    ).insert()
    await Dragon(
        dragon_code="later_but_urgent",
        session_token="s",
        views=0,
        unique_clicks=0,
        time_remaining=5,
        is_sick=False,
    ).insert()

    res = await api_client.get("/api/dragons/geode")
    assert res.status_code == 200
    out = res.json()
    codes = [d["dragon_code"] for d in out]
    # Lower time_remaining should be listed first for urgent dragons.
    assert codes[:2] == ["sooner", "later_but_urgent"]


@pytest.mark.asyncio
async def test_scroll_preview_ok(monkeypatch: pytest.MonkeyPatch, api_client) -> None:
    async def fake_scroll(username: str) -> list[dict[str, object]]:
        assert username == "TestUser"
        return [
            {"dragon_code": "xx1a2", "name": "Egg", "can_add": True},
            {"dragon_code": "yy3b4", "name": "", "can_add": False},
        ]

    monkeypatch.setattr(dragons_api, "fetch_user_young_scroll", fake_scroll)

    res = await api_client.post(
        "/api/dragons/scroll-preview",
        json={"input": "https://dragcave.net/user/TestUser"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["username"] == "TestUser"
    assert len(body["dragons"]) == 2
    assert body["dragons"][0]["dragon_code"] == "xx1a2"
    assert body["dragons"][0]["can_add"] is True
    assert body["dragons"][1]["can_add"] is False


@pytest.mark.asyncio
async def test_scroll_preview_invalid_input(api_client) -> None:
    res = await api_client.post("/api/dragons/scroll-preview", json={"input": "../../"})
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_remove_requires_valid_session_token(monkeypatch: pytest.MonkeyPatch, api_client) -> None:
    async def fake_fetch(code: str) -> _FakeStats:  # noqa: ARG001
        return _FakeStats(views=1, unique_clicks=1, time_remaining=10, is_sick=False)

    monkeypatch.setattr(dragons_api, "fetch_crystal_stats", fake_fetch)
    add = await api_client.post("/api/dragons/add", json={"dragon_codes": ["abCd3"]})
    token = add.json()["session_token"]

    bad = await api_client.request("DELETE", "/api/dragons/remove", json={"session_token": "nope", "dragon_codes": ["abCd3"]})
    assert bad.status_code == 403

    ok = await api_client.request("DELETE", "/api/dragons/remove", json={"session_token": token, "dragon_codes": ["abCd3"]})
    assert ok.status_code == 200
    assert ok.json()["removed"] == ["abCd3"]

