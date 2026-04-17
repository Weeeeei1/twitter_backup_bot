"""Main entry point for the Twitter Backup Bot."""

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


def main() -> None:
    """Main entry point."""
    import asyncio

    logger = logging.getLogger(__name__)
    setup_logging()

    async def async_main():
        """Async main entry point."""
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

        # Create bot application
        app = BotApplication(bot_token=settings.bot_token, db=db, redis=redis)

        logger.info("Bot is ready!")

        # run() handles everything synchronously
        app.run()

    asyncio.run(async_main())


if __name__ == "__main__":
    main()
