import asyncio
import logging
from logging import Logger

from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .modules.monitor.monitor_execution_service import run_monitor_jobs
from .redis.redis import redis_client

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(name)s: %(message)s")
logger: Logger = logging.getLogger("background-main")


async def main() -> None:
    """
    The main coroutine that sets up the scheduler and runs the application's event loop.
    """
    await redis_client.connect()

    scheduler: AsyncIOScheduler = AsyncIOScheduler(
        executors={
            "default": AsyncIOExecutor(),
            "threadpool": ThreadPoolExecutor(10),
        }
    )

    scheduler.add_job(
        run_monitor_jobs,
        trigger="interval",
        seconds=1,
        id="monitor-health-checks",
        max_instances=1,
        coalesce=True,
    )

    scheduler.start()

    logger.info("APScheduler service started. Press Ctrl+C to exit.")

    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        await redis_client.disconnect()
        logger.info("Scheduler shut down gracefully.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Async cron service stopped.")
