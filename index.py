from fastapi import FastAPI
from mangum import Mangum
from api.main import api_app

# Wrap the FastAPI app with Mangum for AWS Lambda compatibility
handler = Mangum(api_app)
