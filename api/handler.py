import logging
from api.main import app

logger = logging.getLogger("vercel_app")
logger.debug("=== Handler initialization ===")


async def handler(scope, receive, send):
    logger.debug(f"=== Handler called with scope: {scope} ===")
    await app(scope, receive, send)
