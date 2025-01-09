import json
import asyncio
import time
import os
import sys
import traceback
from fastapi import FastAPI, Depends
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import logging

# Enhanced logging setup
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more verbose logging
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add system information logging
logger.info(f"Python version: {sys.version}")
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"PYTHONPATH: {sys.path}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Detailed startup logging
    logger.info("=== Starting ASGI Application Initialization ===")

    try:
        # Log environment state
        logger.debug("Environment variables:")
        for key, value in os.environ.items():
            if "KEY" in key.upper() or "SECRET" in key.upper():
                logger.debug(f"{key}: [REDACTED]")
            else:
                logger.debug(f"{key}: {value}")

        # Initialize your services
        logger.info("Initializing services...")
        # Your initialization code here

        logger.info("=== ASGI Application Initialization Complete ===")
        yield

        # Shutdown logging
        logger.info("=== Starting ASGI Application Shutdown ===")
        logger.info("Cleaning up resources...")
        logger.info("=== ASGI Application Shutdown Complete ===")

    except Exception as e:
        logger.error("=== CRITICAL ERROR DURING INITIALIZATION ===")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error("Traceback:")
        logger.error(traceback.format_exc())
        raise


app = FastAPI(lifespan=lifespan)
security = HTTPBearer()


@app.get("/")
async def root():
    logger.info("Handling root request")
    return {"message": "API is running"}


if __name__ == "__main__":
    import uvicorn

    logger.info("=== Starting Development Server ===")
    uvicorn.run(app, host="0.0.0.0", port=8000)
