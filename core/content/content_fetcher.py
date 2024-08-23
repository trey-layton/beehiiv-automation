import aiohttp
import uuid
import logging
from core.content.beehiiv_content import get_beehiiv_post_content
from core.models.account_profile import AccountProfile
from supabase import Client

logger = logging.getLogger(__name__)


async def fetch_beehiiv_content(
    account_profile: AccountProfile, post_id: str, supabase: Client
) -> dict:
    try:
        post_content = get_beehiiv_post_content(account_profile, post_id)

        thumbnail_url = post_content.get("thumbnail_url")
        supabase_thumbnail_url = None

        if thumbnail_url:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(thumbnail_url) as resp:
                        if resp.status == 200:
                            content = await resp.read()
                            file_name = f"{uuid.uuid4()}.jpg"

                            # Upload to Supabase storage
                            upload_result = supabase.storage.from_("thumbnails").upload(
                                file_name, content
                            )

                            # Check if upload was successful
                            if upload_result and not isinstance(upload_result, dict):
                                # Get the public URL of the uploaded image
                                public_url_result = supabase.storage.from_(
                                    "thumbnails"
                                ).get_public_url(file_name)
                                supabase_thumbnail_url = public_url_result
                                logger.info(
                                    f"Thumbnail uploaded successfully: {supabase_thumbnail_url}"
                                )
                            else:
                                logger.error(
                                    f"Error uploading thumbnail: {upload_result}"
                                )
            except Exception as e:
                logger.error(f"Error processing thumbnail: {str(e)}")
                logger.error(f"Full error details: {e.__dict__}")

        content_data = {
            "subscribe_url": account_profile.subscribe_url,
            "free_content": post_content.get("free_content"),
            "web_url": post_content.get("web_url"),
            "thumbnail_url": supabase_thumbnail_url or thumbnail_url,
        }

        return content_data
    except Exception as e:
        logger.error(f"Error while fetching Beehiiv content: {str(e)}")
        raise
