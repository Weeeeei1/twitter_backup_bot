"""Main entry point for the Twitter Backup Bot."""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.bot.application import BotApplication
from src.db.database import Database
from src.cache.redis import RedisClient


def setup_logging() -> None:
    """Configure logging."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


async def init_services() -> tuple:
    """Initialize database and Redis. Returns (db, redis)."""
    logger = logging.getLogger(__name__)

    logger.info("Initializing database...")
    db = Database(settings.database_url)
    await db.init()
    logger.info("Database initialized")

    logger.info("Initializing Redis...")
    redis = RedisClient(settings.redis_url)
    await redis.init()
    logger.info("Redis initialized")

    return db, redis


def main() -> None:
    """Main entry point."""
    logger = logging.getLogger(__name__)
    setup_logging()

    logger.info(f"Starting Twitter Backup Bot {settings.get_version()}")
    logger.info("=" * 50)

    # Initialize services in a temporary event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        db, redis = loop.run_until_complete(init_services())
    finally:
        loop.close()

    # Create bot application
    app = BotApplication(bot_token=settings.bot_token, db=db, redis=redis)

    try:
        logger.info("Bot is ready!")
        # run_polling creates its own event loop internally
        # and properly handles startup/shutdown
        app.run_polling()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        # Cleanup is handled by run_polling() but we close our connections too
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(app.shutdown())
            loop.run_until_complete(redis.close())
            loop.run_until_complete(db.close())
        finally:
            loop.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    main()
