from __future__ import annotations

from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

from backend.app.api.dragons import router as dragons_router
from backend.app.db import init_db
from backend.app.sweeper import attach_sweeper


scheduler = AsyncIOScheduler()

# fastapi-cache2 keeps global state and FastAPI lifespan isn't guaranteed to
# run in test environments using `httpx.ASGITransport`. Initialize cache at
# import time so route decorators always have a configured backend.
FastAPICache.init(InMemoryBackend(), prefix="psc-cache:")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    attach_sweeper(scheduler)
    scheduler.start()
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)


app = FastAPI(title="Pink Sapphire Cove API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api")
async def api_index() -> dict[str, str | list[str]]:
    """Avoid a bare `/api` 404 when poking the server from the browser."""
    return {
        "message": "Pink Sapphire Cove API",
        "docs": "/docs",
        "dragon_routes_base": "/api/dragons",
        "example": "GET /api/dragons/cove",
    }


@app.get("/api/dragons")
async def dragons_api_index() -> dict[str, str | list[str]]:
    """
    Lists concrete dragon endpoints. A request to `/api/dragons` alone used to 404
    because only sub-paths are registered on the router.
    """
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


app.include_router(dragons_router)

