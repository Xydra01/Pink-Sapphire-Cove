from __future__ import annotations

import pytest

from backend.app.integrations import dragoncave_legacy as leg


def test_parse_scroll_username_from_url() -> None:
    assert leg.parse_scroll_username("https://dragcave.net/user/HogNoodle") == "HogNoodle"
    assert leg.parse_scroll_username("http://www.dragcave.net/user/Ab_c-12") == "Ab_c-12"


def test_parse_scroll_username_plain() -> None:
    assert leg.parse_scroll_username("  MyUser99  ") == "MyUser99"
    assert leg.parse_scroll_username("@Some_One") == "Some_One"


def test_parse_scroll_username_rejects_empty() -> None:
    with pytest.raises(ValueError, match="empty"):
        leg.parse_scroll_username("   ")


def test_parse_scroll_username_rejects_unsafe() -> None:
    with pytest.raises(ValueError):
        leg.parse_scroll_username("not a username!")
    with pytest.raises(ValueError):
        leg.parse_scroll_username("user/name")
