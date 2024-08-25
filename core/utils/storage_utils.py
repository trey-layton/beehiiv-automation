from io import BytesIO
from supabase import Client
from PIL import Image
import time


def upload_to_supabase(
    supabase: Client, image: Image, bucket: str, file_name: str
) -> str:
    unique_file_name = f"{file_name.split('.')[0]}_{int(time.time() * 1000)}.png"
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format="PNG")
    img_byte_arr = img_byte_arr.getvalue()

    supabase.storage.from_(bucket).upload(unique_file_name, img_byte_arr)
    return supabase.storage.from_(bucket).get_public_url(unique_file_name)
