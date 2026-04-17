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


async def run_bot() -> None:
    """Run the bot."""
    logger = logging.getLogger(__name__)

    logger.info(f"Starting Twitter Backup Bot {settings.get_version()}")
    logger.info("=" * 50)

    # Initialize database
    logger.info("Initializing database...")
    db = Database(settings.database_url)
    await db.init()
    logger.info("Database initialized")

    # Initialize Redis
    logger.info("Initializing Redis...")
    redis = RedisClient(settings.redis_url)
    await redis.init()
    logger.info("Redis initialized")

    # Initialize and run bot
    logger.info("Initializing bot...")
    app = BotApplication(bot_token=settings.bot_token, db=db, redis=redis)

    try:
        logger.info("Bot is ready!")
        # Use initialize() + start() + idling instead of run_polling()
        # to avoid event loop conflicts in shutdown
        await app.initialize_and_run()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await app.shutdown()
        await redis.close()
        await db.close()
        logger.info("Bot stopped")


def main() -> None:
    """Main entry point."""
    setup_logging()
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
