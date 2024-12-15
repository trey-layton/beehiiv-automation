import logging
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any, List, Optional
import os

from core.utils.storage_utils import upload_to_supabase

logger = logging.getLogger(__name__)


class CarouselGenerator:
    def __init__(self, platform: str, font_path: Optional[str] = None):
        self.platform = platform
        self.max_slides = 8 if platform == "linkedin" else 4
        self.image_size = (1080, 1080)

        # Colors
        self.primary_dark = "#2C4154"  # Dark blue background
        self.primary_light = "#CBD5E1"  # Light gray background
        self.text_colors = {
            self.primary_dark: "#FFFFFF",  # White text on dark
            self.primary_light: "#000000",  # Black text on light
        }

        # Font setup
        self.font_path = font_path or self._get_default_font_path()
        self.heading_size = 72
        self.subheading_size = 36

        # Arrow settings
        self.arrow_color = "#FFFFFF"
        self.arrow_size = (80, 40)
        self.arrow_margin = 40

    def _get_default_font_path(self):
        """Get default system font based on OS"""
        import platform

        system = platform.system()
        if system == "Darwin":  # macOS
            return "/System/Library/Fonts/Helvetica.ttc"
        elif system == "Linux":
            return "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        elif system == "Windows":
            return "C:\\Windows\\Fonts\\arial.ttf"
        else:
            raise OSError(f"Unsupported operating system: {system}")

    def _create_arrow(self, draw: ImageDraw, color: str) -> None:
        """Draw the arrow in bottom right corner"""
        width, height = self.image_size
        margin = self.arrow_margin
        arrow_width, arrow_height = self.arrow_size

        # Arrow coordinates
        x1 = width - margin - arrow_width
        y = height - margin - (arrow_height // 2)
        x2 = width - margin

        # Draw the arrow line
        draw.line([(x1, y), (x2, y)], fill=color, width=3)

        # Draw the arrow head
        draw.line([(x2 - 15, y - 15), (x2, y), (x2 - 15, y + 15)], fill=color, width=3)

    def _wrap_text(self, text: str, max_width: int, font: ImageFont) -> str:
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            current_line.append(word)
            line = " ".join(current_line)
            if font.getlength(line) > max_width:
                current_line.pop()
                lines.append(" ".join(current_line))
                current_line = [word]

        lines.append(" ".join(current_line))
        return "\n".join(lines)

    def _create_slide(self, content: Dict[str, str], slide_index: int) -> Image:
        """Create a single slide with styled text and background."""
        # Alternate background colors
        bg_color = self.primary_dark if slide_index % 2 == 0 else self.primary_light
        text_color = self.text_colors[bg_color]

        img = Image.new("RGB", self.image_size, bg_color)
        draw = ImageDraw.Draw(img)

        # Load fonts
        heading_font = ImageFont.truetype(self.font_path, self.heading_size)
        subheading_font = ImageFont.truetype(self.font_path, self.subheading_size)

        # Get text content
        heading = content.get("heading", "")
        subheading = content.get("subheading", "")

        # Calculate text positions (centered vertically and horizontally)
        margin = 80
        available_width = self.image_size[0] - (2 * margin)

        # Draw heading (main text)
        wrapped_heading = self._wrap_text(heading, available_width, heading_font)
        heading_bbox = draw.multiline_textbbox(
            (0, 0), wrapped_heading, font=heading_font
        )
        heading_height = heading_bbox[3] - heading_bbox[1]

        # If there's a subheading, adjust positioning
        if subheading:
            wrapped_subheading = self._wrap_text(
                subheading, available_width, subheading_font
            )
            subheading_bbox = draw.multiline_textbbox(
                (0, 0), wrapped_subheading, font=subheading_font
            )
            subheading_height = subheading_bbox[3] - subheading_bbox[1]

            total_height = heading_height + subheading_height + 20  # 20px spacing
            start_y = (self.image_size[1] - total_height) // 2

            # Draw heading
            draw.multiline_text(
                (margin, start_y),
                wrapped_heading,
                font=heading_font,
                fill=text_color,
                align="left",
            )

            # Draw subheading
            draw.multiline_text(
                (margin, start_y + heading_height + 20),
                wrapped_subheading,
                font=subheading_font,
                fill=text_color,
                align="left",
            )
        else:
            # Only heading, center it
            start_y = (self.image_size[1] - heading_height) // 2
            draw.multiline_text(
                (margin, start_y),
                wrapped_heading,
                font=heading_font,
                fill=text_color,
                align="left",
            )

        # Add arrow (except for last slide)
        if slide_index < self.max_slides - 1:
            self._create_arrow(draw, text_color)

        return img

    async def generate_carousel(
        self, content: Dict[str, Any], supabase_client
    ) -> List[str]:
        """Generate carousel images and upload to Supabase."""
        try:
            slides = content["content_container"]
            image_urls = []

            for idx, slide in enumerate(slides[: self.max_slides]):
                # Format content for the slide
                slide_content = {
                    "heading": slide.get("heading", slide.get("content", "")),
                    "subheading": slide.get("subheading", ""),
                }

                image = self._create_slide(slide_content, idx)
                # Upload to Supabase and get URL
                filename = f"carousel_{content['post_number']}_{idx}.png"
                url = await upload_to_supabase(
                    supabase_client, image, "carousels", filename
                )
                image_urls.append(url)

            return image_urls

        except Exception as e:
            logger.error(f"Error generating carousel: {str(e)}")
            raise
