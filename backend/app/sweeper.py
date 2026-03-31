from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Iterable, List, Sequence, Tuple

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from backend.app.integrations.dragoncave import CrystalStats, DragonCaveAPIError, fetch_crystal_stats
from backend.app.models import Dragon


SWEEPER_INTERVAL_MINUTES = 10
SWEEPER_BATCH_SIZE = 50
SWEEPER_CONCURRENCY = 10


def _chunked(seq: Sequence[Dragon], size: int) -> Iterable[Sequence[Dragon]]:
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


async def _fetch_batch(dragons: Sequence[Dragon]) -> List[Tuple[Dragon, CrystalStats | Exception]]:
    sem = asyncio.Semaphore(SWEEPER_CONCURRENCY)

    async def fetch_one(d: Dragon) -> Tuple[Dragon, CrystalStats | Exception]:
        async with sem:
            try:
                stats = await fetch_crystal_stats(d.dragon_code)
                return d, stats
            except Exception as e:  # noqa: BLE001
                return d, e

    return await asyncio.gather(*(fetch_one(d) for d in dragons))


async def sweep_dragons_once() -> None:
    """
    Refresh all dragons from Dragon Cave and clean up dead/adult ones.
    """

    dragons = await Dragon.find_all().to_list()
    if not dragons:
        return

    for batch in _chunked(dragons, SWEEPER_BATCH_SIZE):
        results = await _fetch_batch(batch)

        for dragon, result in results:
            if isinstance(result, Exception):
                # Skip problematic dragons for this run; could log in future.
                continue

            stats: CrystalStats = result

            # hoursleft semantics:
            # -1 hidden/frozen/adult, -2 dead (see dragon model comments).
            if stats.time_remaining == -2:
                await dragon.delete()
                continue

            if stats.time_remaining == -1:
                await dragon.delete()
                continue

            dragon.views = stats.views
            dragon.unique_clicks = stats.unique_clicks
            dragon.time_remaining = stats.time_remaining
            dragon.is_sick = stats.is_sick
            dragon.updated_at = datetime.utcnow()
            await dragon.save()


def attach_sweeper(scheduler: AsyncIOScheduler) -> None:
    """
    Register the periodic sweeper job on the given scheduler.
    """

    scheduler.add_job(
        sweep_dragons_once,
        "interval",
        minutes=SWEEPER_INTERVAL_MINUTES,
        id="dragon_sweeper",
        replace_existing=True,
    )

