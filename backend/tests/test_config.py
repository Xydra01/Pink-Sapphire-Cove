from __future__ import annotations

import os

from backend.app.core import get_settings


def test_get_settings_reads_env(monkeypatch) -> None:
    monkeypatch.setenv("DC_API_KEY", "x")
    monkeypatch.setenv("MONGODB_URI", "mongodb://example.invalid:27017")
    monkeypatch.setenv("MONGODB_DB", "unit_test_db")

    s = get_settings()
    assert s.dc_api_key == "x"
    assert s.mongodb_uri == "mongodb://example.invalid:27017"
    assert s.mongodb_db == "unit_test_db"

