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
        # Convert PIL Image to bytes
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format="PNG")
        img_byte_arr = img_byte_arr.getvalue()

        # Generate unique filename using timestamp
        unique_file_name = f"{file_name.split('.')[0]}_{int(time.time() * 1000)}.png"

        # Upload to Supabase
        supabase.storage.from_(bucket).upload(unique_file_name, img_byte_arr)

        # Get and return public URL
        return supabase.storage.from_(bucket).get_public_url(unique_file_name)

    except Exception as e:
        logger.error(f"Error uploading to Supabase: {str(e)}")
        raise
