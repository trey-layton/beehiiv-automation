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
    logger.info("Starting storage initialization...")
    try:
        logger.info("Attempting to list existing buckets...")
        buckets = supabase.storage.list_buckets()

        # Handle SyncBucket objects - get the name attribute directly
        existing_bucket_names = [bucket.name for bucket in buckets]
        logger.info(f"Found existing buckets: {existing_bucket_names}")

        existing_buckets = set(existing_bucket_names)

        for bucket_name, config in BUCKET_CONFIGS.items():
            logger.info(f"Checking bucket '{bucket_name}'...")

            if bucket_name not in existing_buckets:
                logger.info(
                    f"Bucket '{bucket_name}' not found, attempting to create..."
                )
                try:
                    supabase.storage.create_bucket(bucket_name, options=config)
                    logger.info(
                        f"Successfully created bucket '{bucket_name}' with config: {config}"
                    )

                    # Verify bucket was created
                    updated_buckets = supabase.storage.list_buckets()
                    updated_bucket_names = [b.name for b in updated_buckets]
                    if bucket_name in updated_bucket_names:
                        logger.info(
                            f"Verified bucket '{bucket_name}' was created successfully"
                        )
                    else:
                        logger.warning(
                            f"Bucket '{bucket_name}' creation succeeded but not found in updated list"
                        )

                except Exception as e:
                    logger.error(
                        f"Error creating bucket '{bucket_name}': {str(e)}",
                        exc_info=True,
                    )
            else:
                logger.info(
                    f"Bucket '{bucket_name}' already exists, checking permissions..."
                )
                try:
                    # Try to list contents to verify permissions
                    supabase.storage.from_(bucket_name).list()
                    logger.info(
                        f"Successfully verified access to bucket '{bucket_name}'"
                    )
                except Exception as e:
                    logger.error(
                        f"Error accessing existing bucket '{bucket_name}': {str(e)}",
                        exc_info=True,
                    )

    except Exception as e:
        logger.error(f"Error in storage initialization: {str(e)}", exc_info=True)
        # Log the error but don't raise - allow the application to continue starting up
        return False

    return True
