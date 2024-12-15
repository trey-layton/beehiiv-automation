import logging
from supabase import Client
from typing import List, Dict

logger = logging.getLogger(__name__)

BUCKET_CONFIGS = {
    "thumbnails": {
        "public": True,
        "allowedMimeTypes": ["image/*"],
        "fileSizeLimit": "5MB",
    },
    "carousels": {
        "public": True,
        "allowedMimeTypes": ["image/*", "application/pdf"],
        "fileSizeLimit": "2MB",
    },
}


async def init_storage(supabase: Client):
    try:
        buckets = supabase.storage.list_buckets()
        existing_buckets = {bucket["name"] for bucket in buckets}

        for bucket_name, config in BUCKET_CONFIGS.items():
            if bucket_name not in existing_buckets:
                try:
                    supabase.storage.create_bucket(bucket_name, options=config)
                    logger.info(f"Created bucket '{bucket_name}' with config: {config}")
                except Exception as e:
                    logger.error(f"Error creating bucket '{bucket_name}': {str(e)}")
            else:
                logger.info(f"Bucket '{bucket_name}' already exists")
    except Exception as e:
        logger.error(f"Error in storage initialization: {str(e)}")
