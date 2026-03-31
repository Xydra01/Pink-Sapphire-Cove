from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

import backend.app.integrations.dragoncave as dc


class _FakeResponse:
    def __init__(self, status_code: int, payload: Any):
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload) if not isinstance(payload, str) else payload
        self.headers = httpx.Headers({"content-type": "application/json"})

    def json(self) -> Any:
        return self._payload


class _FakeAsyncClient:
    def __init__(self, response: _FakeResponse):
        self._response = response

    async def __aenter__(self) -> "_FakeAsyncClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def get(self, url: str, headers: dict[str, str]) -> _FakeResponse:  # noqa: ARG002
        return self._response


def _patch_client(monkeypatch: pytest.MonkeyPatch, response: _FakeResponse) -> None:
    monkeypatch.setattr(dc, "_auth_headers", lambda: {"Authorization": "Bearer test"})
    monkeypatch.setattr(dc.httpx, "AsyncClient", lambda *args, **kwargs: _FakeAsyncClient(response))  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_fetch_crystal_stats_maps_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "errors": [],
        "views": 123,
        "unique": 45,
        "hoursleft": 12,
    }
    _patch_client(monkeypatch, _FakeResponse(200, payload))

    stats = await dc.fetch_crystal_stats("abCd3")
    assert stats.dragon_code == "abCd3"
    assert stats.views == 123
    assert stats.unique_clicks == 45
    assert stats.time_remaining == 12
    assert stats.is_sick is True


@pytest.mark.asyncio
async def test_fetch_crystal_stats_handles_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_client(monkeypatch, _FakeResponse(500, {"oops": "nope"}))
    with pytest.raises(dc.DragonCaveAPIError):
        await dc.fetch_crystal_stats("abCd3")


@pytest.mark.asyncio
async def test_fetch_crystal_stats_raises_on_api_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {"errors": [[3, "Resource not found"]]}
    _patch_client(monkeypatch, _FakeResponse(200, payload))
    with pytest.raises(dc.DragonCaveAPIError):
        await dc.fetch_crystal_stats("abCd3")


@pytest.mark.asyncio
async def test_fetch_crystal_stats_ignores_notice_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "errors": [[0, "Notice"]],
        "views": 1,
        "unique": 2,
        "hoursleft": -1,
    }
    _patch_client(monkeypatch, _FakeResponse(200, payload))
    stats = await dc.fetch_crystal_stats("abCd3")
    assert stats.is_sick is False


def test_load_httpx_json_object_rejects_html() -> None:
    r = httpx.Response(
        200,
        content=b"<html><body>nope</body></html>",
        headers={"content-type": "text/html; charset=utf-8"},
    )
    with pytest.raises(dc.DragonCaveAPIError, match="expected JSON"):
        dc.load_httpx_json_object(r, "test")


def test_load_httpx_json_object_parses_when_content_type_missing_but_body_is_json() -> None:
    r = httpx.Response(200, content=b'{"errors":[],"views":1,"unique":2,"hoursleft":3}', headers={})
    out = dc.load_httpx_json_object(r, "test")
    assert out["views"] == 1

