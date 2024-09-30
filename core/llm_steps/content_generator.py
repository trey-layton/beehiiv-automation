import logging
from core.models.account_profile import AccountProfile
from core.social_media.twitter.precta_tweet import generate_precta_tweet
from core.social_media.twitter.postcta_tweet import generate_postcta_tweet
from core.social_media.twitter.thread_tweet import generate_thread_tweet
from core.social_media.twitter.long_form_tweet import generate_long_form_tweet
from core.social_media.linkedin.long_form_post import generate_linkedin_post
from core.content.image_generator import generate_image_list, edit_image_list_content
from core.utils.storage_utils import upload_to_supabase
from core.models.content import Content, Post, ContentSegment

logger = logging.getLogger(__name__)


async def generate_content(
    content: Content,
    instructions: dict,
    account_profile: AccountProfile,
    supabase_client,
    **kwargs,
) -> Content:
    logger.info(f"Generating content for content_type: {content.content_type}")
    generated_posts = []
    for post in content.posts:
        logger.info(f"Processing post number: {post.post_number}")
        text = post.segments[
            0
        ].content  # Assuming the first segment contains the main content
        content_type = content.content_type

        if content_type == "precta_tweet":
            generated_content = await generate_precta_tweet(text, account_profile)
        elif content_type == "postcta_tweet":
            generated_content = await generate_postcta_tweet(
                text, account_profile, content.metadata.get("web_url")
            )
        elif content_type == "thread_tweet":
            generated_content = await generate_thread_tweet(
                text, content.metadata.get("web_url"), account_profile
            )
        elif content_type == "long_form_tweet":
            generated_content = await generate_long_form_tweet(text, account_profile)
        elif content_type == "linkedin_long_form_post":
            generated_content = await generate_linkedin_post(text, account_profile)
        elif content_type == "image_list":
            image_list_content = await generate_image_list(text, account_profile)
            edited_content = await edit_image_list_content(image_list_content)
            image = generate_image_list(
                edited_content, save_locally=kwargs.get("save_locally", False)
            )
            file_name = f"image_list_{content.metadata.get('post_id')}.png"
            image_url = upload_to_supabase(supabase_client, image, "images", file_name)
            generated_content = {"content": edited_content, "image_url": image_url}
        else:
            raise ValueError(f"Unsupported content type: {content_type}")

        # Convert generated_content to ContentSegment(s)
        if isinstance(generated_content, str):
            segments = [ContentSegment(type="main_content", content=generated_content)]
        elif isinstance(generated_content, dict):
            segments = [
                ContentSegment(type=key, content=value)
                for key, value in generated_content.items()
            ]
        elif isinstance(generated_content, list):
            segments = [
                ContentSegment(type="content", content=item)
                for item in generated_content
            ]
        else:
            raise ValueError(f"Unexpected generated content format for {content_type}")
        logger.info(f"Content generated for post number: {post.post_number}")
        generated_posts.append(Post(post_number=post.post_number, segments=segments))
    logger.info("Content generation completed")
    return Content(
        posts=generated_posts,
        original_content=content.original_content,
        content_type=content.content_type,
        account_id=content.account_id,
        metadata=content.metadata,
    )
