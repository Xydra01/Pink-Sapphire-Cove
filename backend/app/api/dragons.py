from __future__ import annotations

import asyncio
import re
import secrets
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi_cache.decorator import cache
from pydantic import BaseModel, ConfigDict, Field
from pymongo.errors import DuplicateKeyError

from backend.app.integrations.dragoncave import DragonCaveAPIError, fetch_crystal_stats
from backend.app.integrations.dragoncave_legacy import fetch_user_young_scroll, parse_scroll_username
from backend.app.models import Dragon, UserSession


router = APIRouter(prefix="/api/dragons", tags=["dragons"])


@router.get(
    "",
    summary="Dragon API index",
    description="GET this URL in the browser to confirm the API is running; sub-routes are listed below.",
)
async def dragons_api_index() -> dict[str, str | list[str]]:
    return {
        "endpoints": [
            "POST /api/dragons/add — batch add (JSON body: {\"dragon_codes\": [\"AbCdE\"]})",
            "POST /api/dragons/scroll-preview — JSON body: {\"input\": \"user or https://dragcave.net/user/…\"}",
            "GET /api/dragons/cove",
            "GET /api/dragons/geode",
            "DELETE /api/dragons/remove — JSON body: {\"session_token\": \"…\", \"dragon_codes\": optional}",
        ],
        "openapi": "/docs",
    }


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


class ScrollPreviewRequest(BaseModel):
    """Scroll profile URL (dragcave.net/user/…) or plain username."""

    model_config = ConfigDict(populate_by_name=True)

    # JSON field name remains "input" for the frontend; avoid naming the Python attribute `input`
    # (reserved/builtin-adjacent and can confuse some OpenAPI stacks).
    scroll_input: str = Field(alias="input", min_length=1, max_length=500)


class ScrollDragonPreview(BaseModel):
    dragon_code: str
    name: str = ""
    can_add: bool


class ScrollPreviewResponse(BaseModel):
    username: str
    dragons: list[ScrollDragonPreview]


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


async def _ensure_session(token: str) -> UserSession:
    session = await UserSession.find_one(UserSession.token == token)
    if not session:
        raise HTTPException(status_code=403, detail="Invalid session token.")
    if session.expires_at <= datetime.utcnow():
        raise HTTPException(status_code=403, detail="Session token expired.")
    return session


@router.post("/scroll-preview", response_model=ScrollPreviewResponse)
async def scroll_preview(req: ScrollPreviewRequest) -> ScrollPreviewResponse:
    """
    List eggs and unfrozen hatchlings on a user's public scroll (``user_young`` legacy API).
    Use this to let visitors pick which dragons to add; only dragons with Accept Aid on
    should be added (``can_add``).
    """
    try:
        username = parse_scroll_username(req.scroll_input)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    try:
        rows = await fetch_user_young_scroll(username)
    except DragonCaveAPIError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Scroll preview failed: {e!s}") from e

    dragons = [
        ScrollDragonPreview(dragon_code=r["dragon_code"], name=r["name"], can_add=r["can_add"])
        for r in rows
    ]
    return ScrollPreviewResponse(username=username, dragons=dragons)


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
            try:
                await d.insert()
            except DuplicateKeyError:
                dup = await Dragon.find_one(Dragon.dragon_code == code)
                if dup is None:
                    raise
                dup.session_token = session_token
                dup.views = result.views
                dup.unique_clicks = result.unique_clicks
                dup.time_remaining = result.time_remaining
                dup.is_sick = result.is_sick
                dup.updated_at = datetime.utcnow()
                await dup.save()
                d = dup

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
@cache(expire=60)
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
@cache(expire=60)
async def get_geode() -> list[DragonOut]:
    # Phase 2: rely on persisted urgency metadata.
    # Only dragons explicitly marked urgent are returned, ordered by:
    # - lowest time_remaining first
    # - for ties, higher urgency_score first
    dragons = (
        await Dragon.find(Dragon.is_urgent == True)  # noqa: E712
        .sort("+time_remaining", "-urgency_score")
        .to_list()
    )
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

