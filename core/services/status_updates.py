from supabase import Client as SupabaseClient
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class StatusService:
    def __init__(self, supabase: SupabaseClient):
        self.supabase = supabase

    async def update_status(
        self, content_id: str, content_status: str, error_message: Optional[str] = None
    ):
        """
        Update the status of a content generation process

        Args:
            content_id: The ID of the content being generated
            status: The current status of the generation process
            error_message: Optional error message to store if status update fails
        """
        try:
            update_data = {"content_status": content_status, "updated_at": "now()"}

            if error_message:
                update_data["error_message"] = error_message

            response = (
                self.supabase.table("content")
                .update(update_data)
                .eq("id", content_id)
                .execute()
            )

            logger.info(
                f"Updated content {content_id} content_status to: {content_status}"
            )
            return response

        except Exception as e:
            logger.error(f"Failed to update status for content {content_id}: {str(e)}")
            raise Exception(f"Failed to update content status: {str(e)}")
