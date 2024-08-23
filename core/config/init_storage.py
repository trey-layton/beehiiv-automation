import logging
from supabase import Client, create_client
from typing import List, Dict

logger = logging.getLogger(__name__)


async def init_storage(supabase: Client):
    try:
        buckets = supabase.storage.list_buckets()
        if not any(bucket["name"] == "thumbnails" for bucket in buckets):
            logger.error("The 'thumbnails' bucket does not exist")
        else:
            logger.info("The 'thumbnails' bucket exists")
    except Exception as e:
        logger.error(f"Error checking 'thumbnails' bucket: {str(e)}")
