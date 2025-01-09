import sys
import os
import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Force immediate flush of logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True,
)
logger = logging.getLogger("vercel_app")

# Log at the module level
logger.debug("=== Module initialization starting ===")
logger.info(f"Python version: {sys.version}")
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"PYTHONPATH: {sys.path}")
logger.debug("=== Module initialization complete ===")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.debug("=== Lifespan context manager starting ===")
    try:
        yield
    except Exception as e:
        logger.error(f"Lifespan error: {str(e)}", exc_info=True)
        raise
    finally:
        logger.debug("=== Lifespan context manager ending ===")


# Create app instance with debug logging
logger.debug("=== Creating FastAPI instance ===")
app = FastAPI(lifespan=lifespan, debug=True)
logger.debug("=== FastAPI instance created ===")


@app.get("/")
async def root():
    logger.debug("=== Root endpoint called ===")
    return {"message": "API is running"}


# Add explicit startup event handler
@app.on_event("startup")
async def startup_event():
    logger.debug("=== FastAPI startup event triggered ===")


# Add explicit shutdown event handler
@app.on_event("shutdown")
async def shutdown_event():
    logger.debug("=== FastAPI shutdown event triggered ===")


if __name__ == "__main__":
    import uvicorn

    logger.debug("=== Starting Uvicorn server ===")
    uvicorn.run(app, host="0.0.0.0", port=8000)
else:
    logger.debug(f"=== Module imported as: {__name__} ===")
