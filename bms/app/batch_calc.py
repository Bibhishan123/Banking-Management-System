import logging
from decimal import Decimal
from typing import Callable, Dict, List

import concurrent.futures
import asyncio

from sqlalchemy import select
from . import models

logger = logging.getLogger(__name__)


def _fetch_batch(session_factory: Callable[[], object], offset: int, limit: int):
    sess = session_factory()
    try:
        stmt = select(models.Account).order_by(models.Account.id).limit(limit).offset(offset)
        rows = sess.execute(stmt).scalars().all()
        return rows
    finally:
        try:
            sess.close()
        except Exception:
            logger.exception("Failed to close DB session in _fetch_batch")


def _sum_accounts(accounts: List[models.Account]) -> Decimal:
    total = Decimal("0")
    for a in accounts:
        # account.balance is a Decimal-compatible Numeric type
        total += Decimal(a.balance or 0)
    return total


def total_balance_in_batches_threaded(session_factory: Callable[[], object],
                                        batch_size: int = 10,  
                                        max_workers: int = 4) -> Dict:
    """
    Read accounts in pages of `batch_size` and compute sums using a ThreadPoolExecutor.
    Returns dict with 'batch_sums' (list of floats), 'total' (float), 'batches' (int).
    """
    offset = 0
    batch_sums: List[Decimal] = []
    batches: List[List[models.Account]] = []

    # collect batches first (small memory footprint: holds only references to ORM objects per batch)
    while True:
        batch = _fetch_batch(session_factory, offset, batch_size)
        if not batch:
            break
        batches.append(batch)
        offset += len(batch)
        if len(batch) < batch_size:
            break

    if not batches:
        return {"batch_sums": [], "total": 0.0, "batches": 0}

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = [ex.submit(_sum_accounts, b) for b in batches]
        for f in concurrent.futures.as_completed(futures):
            try:
                s = f.result()
                batch_sums.append(s)
            except Exception:
                logger.exception("Error computing batch sum")

    total = sum(batch_sums, Decimal("0"))
    # convert to floats for JSON-friendly output
    return {
        "batch_sums": [float(x) for x in batch_sums],
        "total": float(total),
        "batches": len(batch_sums),
    }


async def total_balance_in_batches_async(session_factory: Callable[[], object],
                                         batch_size: int = 10,
                                         concurrency: int = 4) -> Dict:
    """
    Async implementation that uses threads for DB-bound work via asyncio.to_thread.
    Returns same structure as threaded version.
    """
    loop = asyncio.get_running_loop()
    offset = 0
    batch_sums: List[Decimal] = []
    sem = asyncio.Semaphore(concurrency)
    tasks = []

    async def _fetch_and_sum(off: int):
        async with sem:  # limit concurrent DB fetch+sum tasks
            accounts = await loop.run_in_executor(None, _fetch_batch, session_factory, off, batch_size)
            if not accounts:
                return None
            s = await loop.run_in_executor(None, _sum_accounts, accounts)
            return s

    # schedule fetches in a sliding-window fashion
    while True:
        accounts = await loop.run_in_executor(None, _fetch_batch, session_factory, offset, batch_size)
        if not accounts:
            break
        tasks.append(asyncio.create_task(_fetch_and_sum(offset)))
        offset += len(accounts)
        if len(accounts) < batch_size:
            break

    if not tasks:
        return {"batch_sums": [], "total": 0.0, "batches": 0}

    results = await asyncio.gather(*tasks, return_exceptions=True)
    for r in results:
        if isinstance(r, Exception):
            logger.exception("Error in async batch sum task: %s", r)
        elif r is not None:
            batch_sums.append(r)

    total = sum(batch_sums, Decimal("0"))
    return {"batch_sums": [float(x) for x in batch_sums], "total": float(total), "batches": len(batch_sums)}
