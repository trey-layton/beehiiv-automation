import requests
import json
from config import get_config
import logging

logger = logging.getLogger(__name__)


def post_linkedin(post_text, access_token, linkedin_member_id):
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }
        payload = {
            "author": f"urn:li:person:{linkedin_member_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": post_text},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }

        response = requests.post(
            "https://api.linkedin.com/v2/ugcPosts", headers=headers, json=payload
        )

        if response.status_code != 201:
            raise Exception(
                "Request returned an error: {} {}".format(
                    response.status_code, response.text
                )
            )

        logger.info("LinkedIn post created successfully!")
        logger.info("Response code: {}".format(response.status_code))

        json_response = response.json()
        logger.debug(json.dumps(json_response, indent=4, sort_keys=True))
    except Exception as e:
        logger.exception("Error while posting on LinkedIn:")
        raise


def get_linkedin_member_id(access_token):
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
        }
        response = requests.get("https://api.linkedin.com/v2/me", headers=headers)

        if response.status_code != 200:
            raise Exception(
                "Request returned an error: {} {}".format(
                    response.status_code, response.text
                )
            )

        json_response = response.json()
        return json_response["id"]
    except Exception as e:
        logger.exception("Error while fetching LinkedIn member ID:")
        raise
