import os
from celery import Celery
from core.main_process import run_main_process
from dotenv import load_dotenv

load_dotenv()

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
app = Celery("tasks", broker=redis_url, backend=redis_url)

@app.task(bind=True, max_retries=3, soft_time_limit=600)
def generate_content_task(self, account_profile, post_id, content_type):
    try:
        success, message, content = run_main_process(
            account_profile, post_id, content_type
        )
        return {"success": success, "message": message, "content": content}
    except Exception as exc:
        self.retry(exc=exc, countdown=60)
