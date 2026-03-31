from __future__ import annotations

import asyncio
import re
import secrets
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.integrations.dragoncave import DragonCaveAPIError, fetch_crystal_stats
from backend.app.models import Dragon, UserSession


router = APIRouter(prefix="/api/dragons", tags=["dragons"])

DRAGON_CODE_RE = re.compile(r"^[A-Za-z0-9]{1,5}$")
FETCH_CONCURRENCY = 10


class AddDragonsRequest(BaseModel):
    dragon_codes: list[str] = Field(min_length=1, max_length=200)


class DragonOut(BaseModel):
    dragon_code: str
    views: int
    unique_clicks: int
    time_remaining: int
    is_sick: bool


class AddDragonsError(BaseModel):
    dragon_code: str
    error: str


class AddDragonsResponse(BaseModel):
    session_token: str
    dragons: list[DragonOut]
    errors: list[AddDragonsError]


class RemoveDragonsRequest(BaseModel):
    session_token: str
    dragon_codes: list[str] | None = None


class RemoveDragonsResponse(BaseModel):
    removed: list[str]


def _validate_dragon_codes(codes: list[str]) -> tuple[list[str], list[AddDragonsError]]:
    valid: list[str] = []
    errors: list[AddDragonsError] = []
    seen: set[str] = set()

    for raw in codes:
        code = (raw or "").strip()
        if not code or not DRAGON_CODE_RE.match(code):
            errors.append(AddDragonsError(dragon_code=raw, error="Invalid dragon code format."))
            continue
        if code in seen:
            continue
        seen.add(code)
        valid.append(code)

    return valid, errors


def _priority_score(d: Dragon) -> float:
    """
    Higher score = higher urgency for the Geode.

    This is intentionally simple for Phase 1; it can be refined later.
    """

    if d.time_remaining < 0:
        return 0.0

    # Eggs/hatchlings with low remaining time should dominate.
    time_term = max(0, 48 - d.time_remaining) * 100.0

    # Low progress gets a boost (avoid div by zero).
    views_term = 50_000.0 / (d.views + 10)
    unique_term = 25_000.0 / (d.unique_clicks + 5)

    return time_term + views_term + unique_term


async def _ensure_session(token: str) -> UserSession:
    session = await UserSession.find_one(UserSession.token == token)
    if not session:
        raise HTTPException(status_code=403, detail="Invalid session token.")
    if session.expires_at <= datetime.utcnow():
        raise HTTPException(status_code=403, detail="Session token expired.")
    return session


@router.post("/add", response_model=AddDragonsResponse)
async def add_dragons(req: AddDragonsRequest) -> AddDragonsResponse:
    valid_codes, errors = _validate_dragon_codes(req.dragon_codes)
    if not valid_codes:
        raise HTTPException(status_code=400, detail="No valid dragon codes provided.")

    session_token = secrets.token_urlsafe(32)
    session = UserSession(token=session_token)
    await session.insert()

    sem = asyncio.Semaphore(FETCH_CONCURRENCY)

    async def fetch_one(code: str) -> tuple[str, Any]:
        async with sem:
            try:
                stats = await fetch_crystal_stats(code)
                return code, stats
            except Exception as e:
                return code, e

    results = await asyncio.gather(*(fetch_one(c) for c in valid_codes))

    dragons_out: list[DragonOut] = []

    for code, result in results:
        if isinstance(result, Exception):
            msg = str(result)
            if isinstance(result, DragonCaveAPIError):
                msg = f"Dragon Cave API: {msg}"
            errors.append(AddDragonsError(dragon_code=code, error=msg))
            continue

        existing = await Dragon.find_one(Dragon.dragon_code == code)
        if existing:
            existing.session_token = session_token
            existing.views = result.views
            existing.unique_clicks = result.unique_clicks
            existing.time_remaining = result.time_remaining
            existing.is_sick = result.is_sick
            existing.updated_at = datetime.utcnow()
            await existing.save()
            d = existing
        else:
            d = Dragon(
                dragon_code=code,
                session_token=session_token,
                views=result.views,
                unique_clicks=result.unique_clicks,
                time_remaining=result.time_remaining,
                is_sick=result.is_sick,
                updated_at=datetime.utcnow(),
            )
            await d.insert()

        dragons_out.append(
            DragonOut(
                dragon_code=d.dragon_code,
                views=d.views,
                unique_clicks=d.unique_clicks,
                time_remaining=d.time_remaining,
                is_sick=d.is_sick,
            )
        )

    return AddDragonsResponse(session_token=session.token, dragons=dragons_out, errors=errors)


@router.get("/cove", response_model=list[DragonOut])
async def get_cove() -> list[DragonOut]:
    dragons = await Dragon.find(Dragon.is_sick == False, Dragon.time_remaining != -2).to_list()  # noqa: E712
    return [
        DragonOut(
            dragon_code=d.dragon_code,
            views=d.views,
            unique_clicks=d.unique_clicks,
            time_remaining=d.time_remaining,
            is_sick=d.is_sick,
        )
        for d in dragons
    ]


@router.get("/geode", response_model=list[DragonOut])
async def get_geode() -> list[DragonOut]:
    # Include eggs/hatchlings with measurable time remaining and anything already flagged.
    dragons = await Dragon.find(
        Dragon.time_remaining >= 0,
        Dragon.time_remaining <= 48,
    ).to_list()

    # Also include explicitly sick (covers threshold changes / older records).
    sick_extra = await Dragon.find(Dragon.is_sick == True).to_list()  # noqa: E712
    by_code = {d.dragon_code: d for d in dragons}
    for d in sick_extra:
        by_code.setdefault(d.dragon_code, d)

    ordered = sorted(by_code.values(), key=_priority_score, reverse=True)
    return [
        DragonOut(
            dragon_code=d.dragon_code,
            views=d.views,
            unique_clicks=d.unique_clicks,
            time_remaining=d.time_remaining,
            is_sick=d.is_sick,
        )
        for d in ordered
    ]


@router.delete("/remove", response_model=RemoveDragonsResponse)
async def remove_dragons(req: RemoveDragonsRequest) -> RemoveDragonsResponse:
    await _ensure_session(req.session_token)

    removed: list[str] = []

    if req.dragon_codes:
        codes, _ = _validate_dragon_codes(req.dragon_codes)
        for code in codes:
            d = await Dragon.find_one(Dragon.dragon_code == code, Dragon.session_token == req.session_token)
            if d:
                await d.delete()
                removed.append(code)
    else:
        dragons = await Dragon.find(Dragon.session_token == req.session_token).to_list()
        for d in dragons:
            await d.delete()
            removed.append(d.dragon_code)

    return RemoveDragonsResponse(removed=removed)

