# cli/main.py

import sys
import os
import logging
import argparse

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from core.main_process import run_main_process
from core.config.user_config import DB_PATH

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Generate and post tweets from Beehiiv content."
    )
    parser.add_argument("user_id", help="User ID for fetching Beehiiv content")
    parser.add_argument(
        "edition_url", help="URL of the specific edition to fetch content for"
    )
    parser.add_argument(
        "--precta",
        action="store_true",
        help="Generate and post pre-newsletter CTA tweet",
    )
    parser.add_argument(
        "--postcta",
        action="store_true",
        help="Generate and post post-newsletter CTA tweet",
    )
    parser.add_argument(
        "--thread", action="store_true", help="Generate and post thread tweets"
    )
    args = parser.parse_args()

    key_path = os.path.join(project_root, "core", "config", "secret.key")

    # We don't need to pass the user_config_path anymore, as it's defined in user_config.py
    success, message = run_main_process(
        args.user_id,
        args.edition_url,
        args.precta,
        args.postcta,
        args.thread,
        key_path,
        DB_PATH,  # Pass the DB_PATH instead of user_config_path
    )

    if success:
        logger.info("CLI operation completed successfully")
    else:
        logger.error(f"CLI operation failed: {message}")


if __name__ == "__main__":
    main()
