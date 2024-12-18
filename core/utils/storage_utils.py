import logging
import os
from io import BytesIO
from supabase import Client
from PIL import Image
import time

logger = logging.getLogger(__name__)


async def upload_to_supabase(
    supabase: Client, image: Image, bucket: str, file_name: str
) -> str:
    """Upload an image to Supabase Storage and return its public URL."""
    try:
        # Log original image details
        logger.info(f"Original image size (width x height): {image.size}")
        logger.info(f"Original image mode: {image.mode}")
        logger.info(
            f"Original image format: {image.format if hasattr(image, 'format') else 'unknown'}"
        )

        # Convert PIL Image to bytes
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format="PNG", quality=100, dpi=(300, 300))
        img_byte_arr.seek(0)

        # Get bytes and log size
        img_bytes = img_byte_arr.getvalue()
        logger.info(f"Byte array size in bytes: {len(img_bytes)}")

        # Generate unique filename using timestamp
        unique_file_name = f"{file_name.split('.')[0]}_{int(time.time() * 1000)}.png"
        logger.info(f"Uploading as: {unique_file_name}")

        # Upload to Supabase
        supabase.storage.from_(bucket).upload(
            unique_file_name, img_bytes, file_options={"content-type": "image/png"}
        )
        logger.info("Successfully uploaded to Supabase")

        # Get and return public URL
        url = supabase.storage.from_(bucket).get_public_url(unique_file_name)
        logger.info(f"Generated public URL: {url}")
        return url

    except Exception as e:
        logger.error(f"Error uploading to Supabase: {str(e)}")
        logger.exception("Full traceback:")
        raise
