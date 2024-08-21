import os
from dotenv import load_dotenv
from celery import Celery

# Load environment variables from .env file
load_dotenv()

# Get Redis URL from environment variable, with a fallback
redis_url = os.getenv("REDIS_URL")

celery_app = Celery(
    "proj",
    broker=redis_url,
    backend=redis_url,
    include=["tasks"],
)

# Optional configuration
celery_app.conf.update(
    result_expires=3600,
)

if __name__ == "__main__":
    celery_app.start()
