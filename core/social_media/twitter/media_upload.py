from requests_oauthlib import OAuth1Session
import json
import logging
import requests
import tempfile
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)


def upload_media(media_url: str, user_config: dict) -> str:
    """
    Uploads media to Twitter from a given URL.

    Args:
        media_url (str): The URL of the media to upload.
        user_config (dict): User configuration dictionary containing Twitter API credentials.

    Returns:
        str: The media ID of the uploaded media.

    Raises:
        Exception: If media download or upload fails.
    """
    temp_file_path = None
    try:
        twitter_oauth = OAuth1Session(
            user_config["twitter_api_key"],
            client_secret=user_config["twitter_api_secret"],
            resource_owner_key=user_config["twitter_access_key"],
            resource_owner_secret=user_config["twitter_access_secret"],
        )

        response = requests.get(media_url)
        if response.status_code != 200:
            raise Exception(
                f"Failed to download media: {response.status_code} {response.text}"
            )

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(response.content)
            temp_file_path = temp_file.name

        with open(temp_file_path, "rb") as file:
            media_data = file.read()

        response = twitter_oauth.post(
            "https://upload.twitter.com/1.1/media/upload.json",
            files={"media": media_data},
        )

        if response.status_code != 200:
            raise Exception(
                f"Media upload returned an error: {response.status_code} {response.text}"
            )

        media_id = json.loads(response.text)["media_id_string"]
        logger.info("Media uploaded successfully!")

        return media_id
    except requests.RequestException as e:
        logger.error(f"Network error while downloading or uploading media: {e}")
        raise
    except Exception as e:
        logger.exception("Error while uploading media:")
        raise
    finally:
        if temp_file_path:
            try:
                os.remove(temp_file_path)
            except Exception as cleanup_error:
                logger.exception("Error cleaning up temporary file:")


def advanced_upload_media(media_url: str, user_config: dict) -> str:
    """
    Advanced method to upload media to Twitter from a given URL.
    This method supports larger file sizes and provides more detailed feedback.

    Args:
        media_url (str): The URL of the media to upload.
        user_config (dict): User configuration dictionary containing Twitter API credentials.

    Returns:
        str: The media ID of the uploaded media.

    Raises:
        Exception: If media download or upload fails.
    """
    try:
        twitter_oauth = OAuth1Session(
            user_config["twitter_api_key"],
            client_secret=user_config["twitter_api_secret"],
            resource_owner_key=user_config["twitter_access_key"],
            resource_owner_secret=user_config["twitter_access_secret"],
        )

        # Download the media
        response = requests.get(media_url)
        if response.status_code != 200:
            raise Exception(
                f"Failed to download media: {response.status_code} {response.text}"
            )

        media_content = response.content
        file_size = len(media_content)

        # INIT
        logger.info("Initializing media upload")
        init_url = "https://upload.twitter.com/1.1/media/upload.json"
        init_data = {
            "command": "INIT",
            "total_bytes": file_size,
            "media_type": "image/jpeg",  # Adjust this based on your media type
        }
        init_response = twitter_oauth.post(init_url, data=init_data)
        if init_response.status_code != 202:
            raise Exception(
                f"Failed to initialize upload: {init_response.status_code} {init_response.text}"
            )

        media_id = init_response.json()["media_id_string"]

        # APPEND
        logger.info("Appending media data")
        append_url = "https://upload.twitter.com/1.1/media/upload.json"
        segment_size = 4 * 1024 * 1024  # 4MB chunks
        for segment_index in range(0, file_size, segment_size):
            chunk = media_content[segment_index : segment_index + segment_size]
            append_data = {
                "command": "APPEND",
                "media_id": media_id,
                "segment_index": segment_index // segment_size,
            }
            files = {"media": chunk}
            append_response = twitter_oauth.post(
                append_url, data=append_data, files=files
            )
            if append_response.status_code != 204:
                raise Exception(
                    f"Failed to append media chunk: {append_response.status_code} {append_response.text}"
                )

        # FINALIZE
        logger.info("Finalizing media upload")
        finalize_url = "https://upload.twitter.com/1.1/media/upload.json"
        finalize_data = {"command": "FINALIZE", "media_id": media_id}
        finalize_response = twitter_oauth.post(finalize_url, data=finalize_data)
        if finalize_response.status_code != 201:
            raise Exception(
                f"Failed to finalize upload: {finalize_response.status_code} {finalize_response.text}"
            )

        logger.info("Media uploaded successfully!")
        return media_id

    except Exception as e:
        logger.exception("Error while uploading media:")
        raise
