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


app.include_router(dragons_router)

