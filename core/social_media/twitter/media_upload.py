from requests_oauthlib import OAuth1Session
import json
import logging
import requests
import tempfile
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)


def upload_media(media_url: str, user_id: str, config: Dict[str, Any]) -> str:
    """
    Uploads media to Twitter from a given URL.

    Args:
        media_url (str): The URL of the media to upload.
        user_id (str): The user ID for retrieving Twitter credentials.
        config (Dict[str, Any]): Configuration dictionary containing Twitter API credentials.

    Returns:
        str: The media ID of the uploaded media.

    Raises:
        Exception: If media download or upload fails.
    """
    temp_file_path = None
    try:
        twitter_api_key = config["twitter_api_key"]
        twitter_api_secret = config["twitter_api_secret"]
        twitter_access_key = config["twitter_access_key"]
        twitter_access_secret = config["twitter_access_secret"]

        response = requests.get(media_url)
        if response.status_code != 200:
            raise Exception(
                f"Failed to download media: {response.status_code} {response.text}"
            )

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(response.content)
            temp_file_path = temp_file.name

        twitter_oauth = OAuth1Session(
            twitter_api_key,
            client_secret=twitter_api_secret,
            resource_owner_key=twitter_access_key,
            resource_owner_secret=twitter_access_secret,
        )

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
