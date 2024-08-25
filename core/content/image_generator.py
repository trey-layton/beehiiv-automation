import json
import os
import re
from typing import Dict, List, Union
from PIL import Image, ImageDraw, ImageFont
import textwrap
import logging
import time
from core.content.language_model_client import call_language_model
from core.models.account_profile import AccountProfile

logger = logging.getLogger(__name__)


async def generate_image_list_content(
    text: str, account_profile: AccountProfile, save_locally: bool = False
) -> tuple:
    system_message = {
        "role": "system",
        "content": "You are an expert content summarizer and formatter. The title must never be more than 31 characters. Each body line must never be more than 60 characters per point. Return your post content with the title prefixed by '*1*' and each body point on a new line. Never use emojis. Also, pass a message to the content editor after you and tell it NOT TO CHANGE YOUR TITLE",
    }
    user_message = {
        "role": "user",
        "content": f"""Take the following newsletter and turn it into a super catchy, viral visual list that hits the key points of the newsletter. 
        
        1. If the article is a list or guide, include every single item. If it's an analysis or essay, include every key point. If it is a news story, include the key details in punchy, numbered bullet-form. 
        
        2. Give the list/post a title with 30 or fewer characters, ideally that has some sort of number in it like '7 Reasons You Should...' or '5 Tips for...'. The title MUST be under 31 characters. If it is not under 31 characters, then the whole things fails and you get fired. 
        
        3. Keep each point in the body to 100 characters or fewer. 
        
        Here's the content to summarize:\n{text} Return your post content with the title prefixed by '*1*' and each body point on a new line.""",
    }

    logger.info(f"Generating image list content for text: {text[:100]}...")
    content = await call_language_model(system_message, user_message)
    logger.info(f"Raw LLM response: {content}")

    # Edit the content before parsing
    logger.info("Editing image list content")
    edited_content = await edit_image_list_content(content)
    logger.info(f"Edited content: {edited_content}")

    parsed_content = parse_content(edited_content)
    logger.info(f"Parsed content: {parsed_content}")

    return parsed_content


CUSTOM_FONT_PATH = "fonts/Lora-VariableFont_wght.ttf"


def get_system_font():
    # Replace this function with a direct return of your custom font path
    return CUSTOM_FONT_PATH


def parse_content(content: Union[str, Dict]) -> Dict[str, Union[str, List[str]]]:
    if isinstance(content, dict):
        return content

    lines = content.split("\n")
    parsed = {"title": "", "body": []}
    current_item = ""

    for line in lines:
        line = line.strip()
        if line.startswith("*1*"):
            parsed["title"] = line.replace("*1*", "").strip()
        elif line:
            if current_item:
                parsed["body"].append(current_item.strip())
            current_item = line
        elif current_item:
            parsed["body"].append(current_item.strip())
            current_item = ""

    if current_item:
        parsed["body"].append(current_item.strip())

    # If no title was found, use the first body item as title
    if not parsed["title"] and parsed["body"]:
        parsed["title"] = parsed["body"].pop(0)

    return parsed


def draw_mixed_text(
    draw, text, font, bold_font, position, fill, max_width, line_spacing=5
):
    x, y = position
    words = text.split()
    space_width = (
        draw.textbbox((0, 0), " ", font=font)[2]
        - draw.textbbox((0, 0), " ", font=font)[0]
    )
    bold_mode = True
    line = ""
    for word in words:
        word_width = (
            draw.textbbox((0, 0), word, font=bold_font if bold_mode else font)[2]
            - draw.textbbox((0, 0), word, font=bold_font if bold_mode else font)[0]
        )
        if ":" in word:
            before, after = word.split(":", 1)
            if line:
                draw.text(
                    (x, y), line, font=bold_font if bold_mode else font, fill=fill
                )
                y += font.size + line_spacing
                x = position[0]
                line = ""
            draw.text((x, y), before + ":", font=bold_font, fill=fill)
            x += (
                draw.textbbox((0, 0), before + ":", font=bold_font)[2]
                - draw.textbbox((0, 0), before + ":", font=bold_font)[0]
            )
            bold_mode = False
            if after:
                line = after + " "
                x += (
                    draw.textbbox((0, 0), after + " ", font=font)[2]
                    - draw.textbbox((0, 0), after + " ", font=font)[0]
                )
        elif x + word_width <= max_width:
            line += word + " "
            x += word_width + space_width
        else:
            draw.text(
                (position[0], y), line, font=bold_font if bold_mode else font, fill=fill
            )
            y += font.size + line_spacing
            x = position[0]
            line = word + " "
            x += word_width + space_width
    if line:
        draw.text(
            (position[0], y), line, font=bold_font if bold_mode else font, fill=fill
        )
        y += font.size + line_spacing
    return y


def generate_image_list(
    content: Union[str, Dict],
    image_size: tuple = (1044, 2048),
    bg_color: str = "#FDF6E3",
    text_color: str = "#000000",
    save_locally: bool = False,
    line_spacing: int = 15,
) -> Image:
    logger.info("Starting image generation")
    logger.info(f"Content received: {content}")

    try:
        if isinstance(content, dict):
            parsed_content = content
        elif isinstance(content, str):
            parsed_content = parse_content(content)
        else:
            raise ValueError(f"Unsupported content type: {type(content)}")

        logger.info(f"Parsed content: {parsed_content}")  # Add this log

        img = Image.new("RGB", image_size, color=bg_color)
        draw = ImageDraw.Draw(img)
        logger.info(f"Created new image with size {image_size}")

        # FONT SIZES - Adjust these to change text size
        title_font_size = 60
        body_font_size = 40

        title_font = ImageFont.truetype(get_system_font(), title_font_size)
        body_font = ImageFont.truetype(get_system_font(), body_font_size)
        bold_font = ImageFont.truetype(get_system_font(), body_font_size)

        # MARGINS AND SPACING - Adjust these to change layout
        margin = 50
        title_body_spacing = 100
        paragraph_spacing = 40
        content_width = image_size[0] - 2 * margin

        total_content_height = 1400
        y_start = (image_size[1] - total_content_height) // 2

        # Draw title
        title = parsed_content.get("title", "")
        wrapped_title = textwrap.wrap(title, width=30)
        title_height = 0
        title_line_spacing = 20  # Add this line for title line spacing

        for line in wrapped_title:
            bbox = draw.textbbox((0, 0), line, font=title_font)
            title_width = bbox[2] - bbox[0]
            line_height = bbox[3] - bbox[1]
            x = (image_size[0] - title_width) // 2
            draw.text(
                (x, y_start + title_height), line, font=title_font, fill=text_color
            )
            title_height += line_height + title_line_spacing  # Add line spacing here

        y_offset = y_start + title_height + title_body_spacing

        # Draw body content
        for i, item in enumerate(parsed_content["body"], start=1):
            logger.info(f"Processing item {i}: {item}")
            formatted_line = f"{i}. {item}"
            logger.info(f"Formatted line: {formatted_line}")

            y_offset = draw_mixed_text(
                draw,
                formatted_line,
                body_font,
                bold_font,
                (margin, y_offset),
                text_color,
                content_width,
                line_spacing=line_spacing,
            )
            y_offset += paragraph_spacing  # Space between main points

        if save_locally:
            os.makedirs("temp_images", exist_ok=True)
            timestamp = int(time.time())
            img_path = f"temp_images/image_list_{timestamp}.jpg"
            img.save(img_path, "JPEG")
            logger.info(f"Image saved locally: {img_path}")
        else:
            logger.info("Image not saved locally (save_locally=False)")

        logger.info("Image generation completed successfully")
        return img

    except Exception as e:
        logger.error(f"Error in generate_image_list: {str(e)}")
        logger.exception("Traceback:")
        raise


async def edit_image_list_content(content: str) -> Dict[str, Union[str, List[str]]]:
    system_message = {
        "role": "system",
        "content": """You are an expert content editor specializing in creating concise, impactful image lists. Your task is to refine the given content into a format suitable for an image-based post. Follow these guidelines:
        1. Title maximum 30 characters that summarizes the main topic, ideally using a hook involving a number. If the title is too long, rewrite it to be less than 30 characters.
        2. No item in the list longer than 120 characters. If one is, try to rewrite it to be less than 120 characters. However, don't truncate the text.
        3. Ensure each point is clear, impactful, and self-contained. Also, ensure parallelism between the items in the list.
        4. Maintain the core message and key insights from the original content.
        5. Use concise language and avoid unnecessary words.
        Return your post content with the title prefixed by '*1*' and each body point on a new line. Make sure to number each of the items in the list with the first being 1. (while still prexifing the title with '*1*')""",
    }

    user_message = {
        "role": "user",
        "content": f"Edit the following content into an image list format:\n\n{content}",
    }

    try:
        response_content = await call_language_model(system_message, user_message)

        if isinstance(response_content, str):
            parsed_content = json.loads(response_content)
        elif isinstance(response_content, dict):
            parsed_content = response_content
        else:
            raise ValueError("Unexpected response format from language model")

        # Ensure the content meets our requirements
        if "title" not in parsed_content or "body" not in parsed_content:
            raise ValueError("Missing required keys in parsed content")

        # Ensure body items are numbered
        parsed_content["body"] = [
            f"{i+1}. {item}" for i, item in enumerate(parsed_content["body"])
        ]

        return parsed_content

    except Exception as e:
        logger.error(f"Error in edit_image_list_content: {str(e)}")
        # If editing fails, return the original content
        return parse_content(content) if isinstance(content, str) else content
