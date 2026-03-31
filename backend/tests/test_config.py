from __future__ import annotations

import os

from backend.app.core import get_settings


def test_get_settings_reads_env(monkeypatch) -> None:
    monkeypatch.setenv("DC_API_KEY", "x")
    monkeypatch.delenv("DC_AUTHORIZATION", raising=False)
    monkeypatch.setenv("MONGODB_URI", "mongodb://example.invalid:27017")
    monkeypatch.setenv("MONGODB_DB", "unit_test_db")

    s = get_settings()
    assert s.dc_api_key == "x"
    assert s.dc_authorization is None
    assert s.mongodb_uri == "mongodb://example.invalid:27017"
    assert s.mongodb_db == "unit_test_db"


def test_dc_api_key_strips_bearer_prefix(monkeypatch) -> None:
    monkeypatch.setenv("DC_API_KEY", "Bearer mysecretkey")
    monkeypatch.delenv("DC_AUTHORIZATION", raising=False)
    monkeypatch.setenv("MONGODB_URI", "mongodb://example.invalid:27017")
    monkeypatch.setenv("MONGODB_DB", "unit_test_db")

    s = get_settings()
    assert s.dc_api_key == "mysecretkey"


def test_dc_api_key_strips_bearer_prefix_case_insensitive(monkeypatch) -> None:
    monkeypatch.setenv("DC_API_KEY", "bEaReR abc")
    monkeypatch.delenv("DC_AUTHORIZATION", raising=False)
    monkeypatch.setenv("MONGODB_URI", "mongodb://example.invalid:27017")
    monkeypatch.setenv("MONGODB_DB", "unit_test_db")

    s = get_settings()
    assert s.dc_api_key == "abc"


def test_dc_authorization_full_bearer_line(monkeypatch) -> None:
    monkeypatch.setenv("DC_API_KEY", "legacy-only-key")
    monkeypatch.setenv("DC_AUTHORIZATION", "Bearer v2-token-xyz")
    monkeypatch.setenv("MONGODB_URI", "mongodb://example.invalid:27017")
    monkeypatch.setenv("MONGODB_DB", "unit_test_db")

    s = get_settings()
    assert s.dc_api_key == "legacy-only-key"
    assert s.dc_authorization == "Bearer v2-token-xyz"


def test_dc_authorization_bare_token_gets_bearer_prefix(monkeypatch) -> None:
    monkeypatch.setenv("DC_API_KEY", "k")
    monkeypatch.setenv("DC_AUTHORIZATION", "just-the-token")
    monkeypatch.setenv("MONGODB_URI", "mongodb://example.invalid:27017")
    monkeypatch.setenv("MONGODB_DB", "unit_test_db")

    s = get_settings()
    assert s.dc_authorization == "Bearer just-the-token"

