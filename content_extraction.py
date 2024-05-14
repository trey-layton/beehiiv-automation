from bs4 import BeautifulSoup
import re
import logging

logger = logging.getLogger(__name__)


def extract_text(html_str):
    try:
        soup = BeautifulSoup(html_str, "html.parser")
        paragraphs = soup.find_all("p", {"class": "paragraph"})

        text = "\n\n".join(paragraph.get_text() for paragraph in paragraphs)
        text = re.sub(r"_.*?_", "", text)
        text = re.sub(r"https?://\S+", "", text)
        text = re.sub(r"\n\s*\n", "\n", text, flags=re.MULTILINE)

        return text.strip()
    except Exception as e:
        logger.exception("Error while extracting text from HTML:")
        raise
