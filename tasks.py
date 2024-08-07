from celery import Celery
from core.main_process import run_main_process

app = Celery(
    "tasks",
    broker="redis://default:cA9rxpr0gB4AeW2JFSTkoQuw6ZLhJ1Wq@redis-17705.c263.us-east-1-2.ec2.redns.redis-cloud.com:17705",
)


@app.task
def generate_content_task(
    user_config,
    edition_url,
    precta_tweet,
    postcta_tweet,
    thread_tweet,
    long_form_tweet,
    linkedin,
):
    success, message, content = run_main_process(
        user_config,
        edition_url,
        precta_tweet,
        postcta_tweet,
        thread_tweet,
        long_form_tweet,
        linkedin,
    )
    return {"success": success, "message": message, "content": content}
