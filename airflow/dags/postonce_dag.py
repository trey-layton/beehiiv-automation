from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup
from airflow.models import Variable
from datetime import datetime, timedelta
import logging
from fastapi.params import Param
from api.main import get_supabase_client
from core.content.content_fetcher import fetch_beehiiv_content
from core.content.improved_llm_flow.casual_editor import casual_edit
from core.content.improved_llm_flow.json_converter import convert_to_json
from core.social_media.twitter.tweet_handler import TweetHandler
from core.social_media.linkedin.generate_linkedin_post import generate_linkedin_post
import os
import sys

from social_media.twitter.generate_tweets import (
    generate_long_form_tweet,
    generate_postcta_tweet,
    generate_precta_tweet,
    generate_thread_tweet,
)

supabase_url = Variable.get("SUPABASE_URL")
supabase_key = Variable.get("SUPABASE_KEY")

logger = logging.getLogger(__name__)

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

default_args = {
    "owner": "postonce",
    "depends_on_past": False,
    "start_date": datetime(2023, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "postonce_workflow",
    default_args=default_args,
    description="PostOnce content generation and posting workflow",
    schedule_interval=None,
    params={
        "user_id": Param("", type="string"),
        "edition_url": Param("", type="string"),
    },
)


def log_task_info(**context):
    task_instance = context["task_instance"]
    task_id = context["task"].task_id
    xcom_value = task_instance.xcom_pull(task_ids=task_id)
    logging.info(f"Task {task_id} completed. Output: {xcom_value}")


def fetch_content(**context):
    try:
        user_id = context["params"]["user_id"]
        edition_url = context["params"]["edition_url"]

        supabase_client = get_supabase_client()
        user_profile = (
            supabase_client.table("user_profiles")
            .select("*")
            .eq("id", user_id)
            .execute()
        )

        if not user_profile.data:
            raise ValueError(f"User profile not found for user ID: {user_id}")

        user_config = user_profile.data[0]

        logger.info(f"Fetching content for user {user_id} from Beehiiv")
        content_data = fetch_beehiiv_content(user_config, edition_url)

        if not content_data:
            raise ValueError("Failed to fetch content from Beehiiv")

        context["ti"].xcom_push(key="content", value=content_data)
        context["ti"].xcom_push(key="user_config", value=user_config)
        logger.info("Content fetched successfully")
    except Exception as e:
        logger.exception(f"Error in fetch_content: {str(e)}")
        raise


def generate_twitter_content(**kwargs):
    try:
        ti = kwargs["ti"]
        content_data = ti.xcom_pull(key="content", task_ids="fetch_content")
        user_config = ti.xcom_pull(key="user_config", task_ids="fetch_content")

        original_content = content_data.get("free_content")
        classification = (
            "Daily analysis"  # You might want to implement a classification function
        )

        logger.info("Generating Twitter content")
        precta_tweet = generate_precta_tweet(
            original_content, user_config, classification
        )
        postcta_tweet = generate_postcta_tweet(
            original_content, user_config, classification
        )
        thread_tweet = generate_thread_tweet(
            original_content, content_data.get("web_url"), user_config, classification
        )
        long_form_tweet = generate_long_form_tweet(
            original_content, user_config, classification
        )

        twitter_content = {
            "precta": precta_tweet,
            "postcta": postcta_tweet,
            "thread": thread_tweet,
            "long_form": long_form_tweet,
        }
        ti.xcom_push(key="twitter_content", value=twitter_content)
        logger.info("Twitter content generated successfully")
    except Exception as e:
        logger.exception(f"Error in generate_twitter_content: {str(e)}")
        raise


def generate_linkedin_content(**kwargs):
    try:
        ti = kwargs["ti"]
        content_data = ti.xcom_pull(key="content", task_ids="fetch_content")
        user_config = ti.xcom_pull(key="user_config", task_ids="fetch_content")

        original_content = content_data.get("free_content")
        classification = (
            "Daily analysis"  # You might want to implement a classification function
        )

        logger.info("Generating LinkedIn content")
        linkedin_post = generate_linkedin_post(
            original_content, user_config, classification
        )

        ti.xcom_push(key="linkedin_content", value=linkedin_post)
        logger.info("LinkedIn content generated successfully")
    except Exception as e:
        logger.exception(f"Error in generate_linkedin_content: {str(e)}")
        raise


def post_to_twitter(**kwargs):
    try:
        ti = kwargs["ti"]
        twitter_content = ti.xcom_pull(
            key="twitter_content", task_ids="generate_twitter_content"
        )
        user_config = ti.xcom_pull(key="user_config", task_ids="fetch_content")
        content_data = ti.xcom_pull(key="content", task_ids="fetch_content")

        # Retrieve Twitter credentials from user_config
        twitter_credentials = {
            "api_key": user_config["twitter_api_key"],
            "api_secret": user_config["twitter_api_secret"],
            "access_token": user_config["twitter_access_token"],
            "access_token_secret": user_config["twitter_access_token_secret"],
        }

        tweet_handler = TweetHandler(twitter_credentials)

        logger.info("Posting to Twitter")
        tweet_handler.post_pre_cta_tweet(
            twitter_content["precta"], user_config["subscribe_url"]
        )
        tweet_handler.post_post_cta_tweet(
            twitter_content["postcta"],
            content_data["web_url"],
            content_data["thumbnail_url"],
        )
        tweet_handler.post_thread(twitter_content["thread"], content_data["web_url"])

        logger.info("Twitter content posted successfully")
    except Exception as e:
        logger.exception(f"Error in post_to_twitter: {str(e)}")
        raise


def post_to_linkedin(**kwargs):
    try:
        ti = kwargs["ti"]
        linkedin_content = ti.xcom_pull(
            key="linkedin_content", task_ids="generate_linkedin_content"
        )
        user_config = ti.xcom_pull(key="user_config", task_ids="fetch_content")

        # Retrieve LinkedIn credentials from user_config
        linkedin_credentials = {
            "access_token": user_config["linkedin_access_token"],
            # Add any other necessary LinkedIn credentials
        }

        logger.info("Posting to LinkedIn")
        # Implement LinkedIn posting logic here
        # For example: post_linkedin(linkedin_content, linkedin_credentials)

        logger.info("LinkedIn content posted successfully")
    except Exception as e:
        logger.exception(f"Error in post_to_linkedin: {str(e)}")
        raise


def classify_and_summarize(**context):
    ti = context["ti"]
    content = ti.xcom_pull(key="content", task_ids="fetch_content")
    classification_result = classify_and_summarize(content)
    ti.xcom_push(key="classification", value=classification_result)


with dag:
    fetch_content_task = PythonOperator(
        task_id="fetch_content",
        python_callable=fetch_content,
        provide_context=True,
    )

    classify_task = PythonOperator(
        task_id="classify_content",
        python_callable=classify_and_summarize,
        provide_context=True,
    )

    with TaskGroup("generate_twitter_content") as generate_twitter_content:
        for content_type in ["precta", "postcta", "thread", "long_form"]:

            casual_edit_task = PythonOperator(
                task_id=f"casual_edit_{content_type}",
                python_callable=casual_edit,
                op_kwargs={"content_type": content_type},
                provide_context=True,
            )

            json_convert_task = PythonOperator(
                task_id=f"json_convert_{content_type}",
                python_callable=convert_to_json,
                op_kwargs={"content_type": content_type},
                provide_context=True,
            )

            casual_edit_task >> json_convert_task

    generate_linkedin_task = PythonOperator(
        task_id="generate_linkedin_content",
        python_callable=generate_linkedin_content,
        provide_context=True,
    )

    post_twitter_task = PythonOperator(
        task_id="post_to_twitter",
        python_callable=post_to_twitter,
        provide_context=True,
    )

    post_linkedin_task = PythonOperator(
        task_id="post_to_linkedin",
        python_callable=post_to_linkedin,
        provide_context=True,
    )

    (
        fetch_content_task
        >> classify_task
        >> [generate_twitter_content, generate_linkedin_task]
    )
    generate_twitter_content >> post_twitter_task
    generate_linkedin_task >> post_linkedin_task

    # Add log_task_info to each task
    for task in dag.tasks:
        log_task = PythonOperator(
            task_id=f"log_{task.task_id}",
            python_callable=log_task_info,
            provide_context=True,
        )
        task >> log_task
