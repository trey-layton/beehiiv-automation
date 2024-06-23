import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def clean_html_content(html_content: str) -> str:
    """
    Cleans the HTML content and extracts text.

    Args:
        html_content (str): The HTML content to clean.

    Returns:
        str: The cleaned text content from the HTML.
    """
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        text_elements = soup.find_all(["h1", "h2", "h3", "p", "li"])
        clean_text = "\n".join([element.get_text() for element in text_elements])
        return clean_text
    except Exception as e:
        logger.exception("Error while cleaning HTML content:")
        raise
