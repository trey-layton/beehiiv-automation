import logging
import json

logger = logging.getLogger("vercel_app")
logger.debug("=== Pure ASGI Handler initialization ===")


async def app(scope, receive, send):
    logger.debug(f"=== ASGI app called with scope type: {scope['type']} ===")

    if scope["type"] == "http":
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    [b"content-type", b"application/json"],
                ],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": json.dumps({"message": "Hello from minimal ASGI"}).encode(),
            }
        )


handler = app
