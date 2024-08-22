import sys
import os
import logging
import argparse

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from core.main_process import run_main_process

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

    success, message = run_main_process(
        args.user_id,
        args.edition_url,
        args.precta,
        args.postcta,
        args.thread,
    )

    if success:
        logger.info("CLI operation completed successfully")
        print(message)
    else:
        logger.error(f"CLI operation failed: {message}")
        print(f"Error: {message}")


if __name__ == "__main__":
    main()
