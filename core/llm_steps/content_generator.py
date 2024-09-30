from core.models.account_profile import AccountProfile
from core.social_media.twitter.precta_tweet import generate_precta_tweet
from core.social_media.twitter.postcta_tweet import generate_postcta_tweet
from core.social_media.twitter.thread_tweet import generate_thread_tweet
from core.social_media.twitter.long_form_tweet import generate_long_form_tweet
from core.social_media.linkedin.long_form_post import generate_linkedin_post
from core.content.image_generator import generate_image_list, edit_image_list_content
from core.utils.storage_utils import upload_to_supabase


async def generate_content(
    content_type: str,
    text: str,
    account_profile: AccountProfile,
    supabase_client,
    **kwargs,
):
    if content_type == "precta_tweet":
        return await generate_precta_tweet(text, account_profile)
    elif content_type == "postcta_tweet":
        return await generate_postcta_tweet(
            text, account_profile, kwargs.get("web_url")
        )
    elif content_type == "thread_tweet":
        return await generate_thread_tweet(text, kwargs.get("web_url"), account_profile)
    elif content_type == "long_form_tweet":
        return await generate_long_form_tweet(text, account_profile)
    elif content_type == "linkedin":
        return await generate_linkedin_post(text, account_profile)
    elif content_type == "image_list":
        image_list_content = await generate_image_list(text, account_profile)
        edited_content = await edit_image_list_content(image_list_content)
        image = generate_image_list(
            edited_content, save_locally=kwargs.get("save_locally", False)
        )
        file_name = f"image_list_{kwargs.get('post_id')}.png"
        image_url = upload_to_supabase(supabase_client, image, "images", file_name)
        return {"content": edited_content, "image_url": image_url}
    else:
        raise ValueError(f"Unsupported content type: {content_type}")
