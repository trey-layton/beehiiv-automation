from fastapi import FastAPI
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("vercel_app")

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


# This is the handler that Vercel will call
handler = app
