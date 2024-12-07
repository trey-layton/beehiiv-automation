import json
import logging
from typing import Dict, Any, List, Optional
from supabase import Client as SupabaseClient
from core.content.content_fetcher import fetch_beehiiv_content
from core.models.account_profile import AccountProfile
from core.llm_steps.structure_analysis import analyze_structure
from core.llm_steps.content_strategy import determine_content_strategy
from core.llm_steps.content_generator import generate_content
from core.llm_steps.content_personalization import (
    personalize_content,
    get_instructions_for_content_type,
)
from core.llm_steps.hook_writer import write_hooks
from core.llm_steps.ai_polisher import ai_polish
from core.services.status_updates import StatusService  # Add this import

logger = logging.getLogger(__name__)


async def run_main_process(
    account_profile: AccountProfile,
    content_id: str,  # Add this
    post_id: Optional[str],
    content_type: str,
    supabase: SupabaseClient,
    content: Optional[str] = None,
) -> Dict[str, Any]:
    status_service = StatusService(supabase)

    try:
        # Step 1: Fetch content
        await status_service.update_status(content_id, "analyzing")
        if post_id:
            content_data = await fetch_beehiiv_content(
                account_profile, post_id, supabase
            )
            original_content = content_data.get("free_content")
            web_url = content_data.get("web_url")
            thumbnail_url = content_data.get("thumbnail_url")
        else:
            original_content = content
            web_url = None
            thumbnail_url = None
            post_id = "pasted-content"

        if not original_content:
            await status_service.update_status(content_id, "failed")
            return {"error": "No content found", "success": False}

        # Step 2: Analyze structure
        await status_service.update_status(content_id, "analyzing_structure")
        newsletter_structure: str = await analyze_structure(original_content)

        # Step 3: Determine strategy
        await status_service.update_status(content_id, "determining_strategy")
        content_strategy: str = await determine_content_strategy(newsletter_structure)

        try:
            strategy_list = json.loads(content_strategy)
            if not isinstance(strategy_list, list):
                await status_service.update_status(content_id, "failed")
                return {"error": "Content strategy is not a list", "success": False}
        except json.JSONDecodeError as e:
            await status_service.update_status(content_id, "failed")
            return {"error": "Failed to parse content strategy", "success": False}

        content_type_instructions = get_instructions_for_content_type(content_type)
        generated_contents: List[dict] = []

        # Step 4: Generation loop
        await status_service.update_status(content_id, "generating")
        for strategy in strategy_list:
            post_number = strategy.get("post_number", "unknown")
            try:
                generated_content = await generate_content(
                    strategy, content_type, account_profile, web_url, post_number
                )
                if (
                    not generated_content
                    or "content_container" not in generated_content
                ):
                    continue

                # Step 5: Personalization
                await status_service.update_status(content_id, "personalizing")
                personalized_content = await personalize_content(
                    generated_content,
                    account_profile,
                    content_type,
                    content_type_instructions,
                )
                content_to_use = personalized_content.get(
                    "content_container", generated_content["content_container"]
                )

                # Step 6: Hooks
                await status_service.update_status(content_id, "writing_hooks")
                content_with_hooks = await write_hooks(
                    {"post_number": post_number, "content_container": content_to_use},
                    account_profile,
                    content_type,
                    content_type_instructions,
                )
                content_for_polish = content_with_hooks.get(
                    "content_container", content_to_use
                )

                # Step 7: Polish
                await status_service.update_status(content_id, "polishing")
                polished_content = await ai_polish(
                    {
                        "post_number": post_number,
                        "content_container": content_for_polish,
                    },
                    account_profile,
                    content_type,
                    content_type_instructions,
                )
                final_content_to_use = polished_content.get(
                    "content_container", content_for_polish
                )

                generated_contents.append(
                    {
                        "post_number": post_number,
                        "post_content": final_content_to_use,
                    }
                )

            except Exception as e:
                logger.error(f"Error processing post {post_number}: {str(e)}")
                continue

        if not generated_contents:
            await status_service.update_status(content_id, "failed")
            return {"error": "Failed to generate any valid content", "success": False}

        final_content = {
            "provider": "twitter" if "tweet" in content_type else "linkedin",
            "type": content_type,
            "content": generated_contents,
            "thumbnail_url": thumbnail_url or "",
            "metadata": {"web_url": web_url or "", "post_id": post_id},
            "success": True,
        }

        await status_service.update_status(content_id, "generated")
        return final_content

    except Exception as e:
        await status_service.update_status(content_id, "failed")
        return {"error": str(e), "success": False}
