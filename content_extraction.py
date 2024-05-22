from bs4 import BeautifulSoup
import re
import logging

logger = logging.getLogger(__name__)


def extract_text(html_str):
    try:
        logger.info(
            f"Original HTML content: {html_str[:500]}..."
        )  # Print the first 500 characters to avoid too much output

        soup = BeautifulSoup(html_str, "html.parser")

        # Extract text from all <p> tags
        paragraphs = soup.find_all("p")

        logger.info(f"Found {len(paragraphs)} paragraphs")

        text = "\n\n".join(paragraph.get_text() for paragraph in paragraphs)
        text = re.sub(r"_.*?_", "", text)
        text = re.sub(r"https?://\S+", "", text)
        text = re.sub(r"\n\s*\n", "\n", text, flags=re.MULTILINE)

        cleaned_text = text.strip()
        logger.info(
            f"Cleaned text: {cleaned_text[:500]}..."
        )  # Print the first 500 characters of the cleaned text

        return cleaned_text
    except Exception as e:
        logger.exception("Error while extracting text from HTML:")
        raise
