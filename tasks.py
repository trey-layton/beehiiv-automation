from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

app = Celery('tasks', broker=os.getenv('REDIS_URL'))

@app.task
def add(x, y):
    return x + y
