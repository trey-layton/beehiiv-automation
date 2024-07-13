import aiohttp
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

API_URL = "https://app.stack-auth.com/api/v1"
PROJECT_ID = os.getenv("STACK_PROJECT_ID")
SERVER_KEY = os.getenv("STACK_SECRET_SERVER_KEY")


class StackAuthClient:
    def __init__(self):
        self.session = None

    async def ensure_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def register(self, email, password, discord_id):
        await self.ensure_session()
        url = f"{API_URL}/users"
        headers = {
            "Authorization": f"Bearer {SERVER_KEY}",
            "Content-Type": "application/json",
        }
        data = {
            "project": PROJECT_ID,
            "email": email,
            "password": password,
            "clientMetadata": {"discordId": discord_id},
        }
        logger.debug(f"Sending registration request to: {url}")
        try:
            async with self.session.post(url, json=data, headers=headers) as response:
                status = response.status
                content = await response.text()
                logger.debug(f"Response status: {status}")
                logger.debug(f"Response content: {content}")
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Error during request: {str(e)}")
            raise

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None


stackAuthClient = StackAuthClient()
