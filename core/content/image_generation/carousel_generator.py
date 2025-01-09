import io
import logging
import time
from PIL import Image, ImageDraw, ImageFont
from PIL.ImageFont import FreeTypeFont
from typing import Dict, Any, List, Optional
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from typing import Tuple, List

from core.utils.storage_utils import upload_to_supabase

logger = logging.getLogger(__name__)


class CarouselGenerator:
    def __init__(self, platform: str, font_path: Optional[str] = None):
        self.platform = platform
        self.max_slides = 8 if platform == "linkedin" else 4
        self.image_size = (1200, 1500)  # Slide size

        # Color scheme
        self.primary_dark = "#2B3A4D"  # Dark blue background
        self.text_color = "#FFFFFF"  # White text

        # Font paths (update if needed)
        self.font_path = font_path or "./fonts/Lora-VariableFont_wght.ttf"

        # Slightly smaller initial font sizes so longer text can fit more easily
        self.heading_size_initial = 80
        self.subheading_size_initial = 48

        # Arrow settings
        self.arrow_color = "#FFFFFF"
        self.arrow_width = 3
        self.arrow_size = (60, 30)
        self.arrow_margin = 60

        # Margins & spacing
        self.side_margin = 100
        self.line_spacing = 1.2  # multiplier for line spacing

    def _create_arrow(self, draw: ImageDraw) -> None:
        """Draw a minimal arrow in bottom-right corner."""
        width, height = self.image_size
        margin = self.arrow_margin

        x1 = width - margin - self.arrow_size[0]
        x2 = width - margin
        y = height - margin

        draw.line([(x1, y), (x2, y)], fill=self.arrow_color, width=self.arrow_width)
        draw.line(
            [(x2 - 20, y - 20), (x2, y), (x2 - 20, y + 20)],
            fill=self.arrow_color,
            width=self.arrow_width,
        )

    def _wrap_text(
        self, text: str, font: ImageFont, max_width: int, draw: ImageDraw
    ) -> List[str]:
        """
        Manually wrap text to fit `max_width` using the provided font.
        Returns a list of lines that fit within the width.
        """
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            # Measure text width with current font
            w, _ = draw.textsize(test_line, font=font)
            if w <= max_width:
                current_line.append(word)
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
        lines.append(" ".join(current_line))

        return lines

    def _fit_text_box(
        self,
        draw: ImageDraw,
        text: str,
        x: int,
        y: int,
        box_width: int,
        box_height: int,
        initial_font_size: int,
    ) -> Tuple[ImageFont.ImageFont, List[str]]:
        """
        Attempt to fit the entire 'text' inside the (box_width x box_height) area,
        reducing font size as needed. Returns a tuple of (final_font, wrapped_lines).
        """
        # Start from the initial size, go down if needed
        font_size = initial_font_size
        min_font_size = 18  # Don't go below this to avoid unreadably small text

        while font_size >= min_font_size:
            font = ImageFont.truetype(self.font_path, font_size)
            wrapped_lines = self._wrap_text(text, font, box_width, draw)

            # Calculate total height
            line_height = font.getmetrics()[0] + font.getmetrics()[1]
            total_height = len(wrapped_lines) * line_height * self.line_spacing

            if total_height <= box_height:
                # Found a size that fits
                return font, wrapped_lines

            font_size -= 2

        # If we exit loop, it means text is too long even at min font size
        # We'll still return the min font and the wrapped lines (though it may overflow)
        font = ImageFont.truetype(self.font_path, min_font_size)
        wrapped_lines = self._wrap_text(text, font, box_width, draw)
        return font, wrapped_lines

    def _draw_multiline_text(
        self,
        draw: ImageDraw,
        lines: List[str],
        font: ImageFont,
        x: int,
        start_y: int,
        line_spacing: float,
        fill_color: str,
    ) -> int:
        """
        Draw multiline text line by line, returning the total height consumed.
        """
        _, baseline = font.getmetrics()
        line_height = baseline + font.getmetrics()[0]
        total_height = 0

        current_y = start_y
        for line in lines:
            draw.text((x, current_y), line, font=font, fill=fill_color)
            current_y += line_height * line_spacing
            total_height += line_height * line_spacing

        return int(total_height)

    def _create_slide(self, content: Dict[str, str], slide_index: int) -> Image:
        """Create a single slide with improved text handling for longer content."""
        img = Image.new("RGB", self.image_size, self.primary_dark)
        draw = ImageDraw.Draw(img)

        heading_text = content.get("heading", "")
        subheading_text = content.get("subheading", "")

        # Define bounding boxes for heading and subheading
        # We'll allocate about half the slide for heading, half for subheading
        # (You can adjust these proportions to your liking).
        heading_box_height = self.image_size[1] // 3
        subheading_box_height = self.image_size[1] // 2

        # Fit heading text
        heading_font, heading_lines = self._fit_text_box(
            draw=draw,
            text=heading_text,
            x=self.side_margin,
            y=self.side_margin,
            box_width=self.image_size[0] - 2 * self.side_margin,
            box_height=heading_box_height,
            initial_font_size=self.heading_size_initial,
        )

        # Calculate how many pixels heading actually occupies
        heading_total_height = (
            len(heading_lines)
            * (heading_font.getmetrics()[0] + heading_font.getmetrics()[1])
            * self.line_spacing
        )

        # Fit subheading text
        subheading_font, subheading_lines = self._fit_text_box(
            draw=draw,
            text=subheading_text,
            x=self.side_margin,
            y=self.side_margin + int(heading_total_height) + 40,
            box_width=self.image_size[0] - 2 * self.side_margin,
            box_height=subheading_box_height,
            initial_font_size=self.subheading_size_initial,
        )

        # Now that we have both sets of lines, we’ll center them vertically in total
        total_content_height = heading_total_height + 40
        line_height_sub = (
            subheading_font.getmetrics()[0] + subheading_font.getmetrics()[1]
        ) * self.line_spacing
        total_content_height += len(subheading_lines) * line_height_sub

        start_y = (self.image_size[1] - total_content_height) // 2

        # Draw heading lines
        heading_height_drawn = self._draw_multiline_text(
            draw=draw,
            lines=heading_lines,
            font=heading_font,
            x=self.side_margin,
            start_y=start_y,
            line_spacing=self.line_spacing,
            fill_color=self.text_color,
        )

        # Spacing between heading and subheading
        sub_start_y = start_y + heading_height_drawn + 40

        # Draw subheading lines
        self._draw_multiline_text(
            draw=draw,
            lines=subheading_lines,
            font=subheading_font,
            x=self.side_margin,
            start_y=sub_start_y,
            line_spacing=self.line_spacing,
            fill_color=self.text_color,
        )

        # Add arrow if it's not the last slide
        if slide_index < self.max_slides - 1:
            self._create_arrow(draw)

        return img

    async def generate_carousel(
        self, content: Dict[str, Any], supabase_client
    ) -> List[str]:
        """Generate carousel images and upload to Supabase."""
        try:
            slides = content["content_container"]
            if self.platform == "linkedin":
                post_images = []
                for idx, slide in enumerate(slides[: self.max_slides]):
                    slide_content = {
                        "heading": slide.get("heading", slide.get("content", "")),
                        "subheading": slide.get("subheading", ""),
                    }
                    image = self._create_slide(slide_content, idx)
                    post_images.append(image)

                # Generate PDF for LinkedIn
                pdf_data = await self.generate_pdf_from_images(post_images)

                # Upload PDF to Supabase
                timestamp = int(time.time() * 1000)
                filename = f"carousel_{content['post_number']}_{timestamp}.pdf"
                supabase_client.storage.from_("carousels").upload(
                    filename, pdf_data, file_options={"content-type": "application/pdf"}
                )

                # Get public URL
                url = supabase_client.storage.from_("carousels").get_public_url(
                    filename
                )
                return [url]
            else:
                image_urls = []
                for idx, slide in enumerate(slides[: self.max_slides]):
                    slide_content = {
                        "heading": slide.get("heading", slide.get("content", "")),
                        "subheading": slide.get("subheading", ""),
                    }
                    image = self._create_slide(slide_content, idx)
                    filename = f"carousel_{content['post_number']}_{idx}.png"
                    url = await upload_to_supabase(
                        supabase_client, image, "carousels", filename
                    )
                    image_urls.append(url)

                return image_urls

        except Exception as e:
            logger.error(f"Error generating carousel: {str(e)}")
            raise

    async def generate_pdf_from_images(self, image_list: List[Image.Image]) -> bytes:
        """Convert a list of PIL Images into a single PDF."""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)

        for img in image_list:
            img_buffer = io.BytesIO()
            img.save(img_buffer, format="PNG")
            img_buffer.seek(0)

            img_width, img_height = img.size
            aspect = img_height / float(img_width)

            page_width = letter[0]
            page_height = letter[1]

            # Calculate dimensions to fit page while preserving aspect ratio
            if aspect > 1:
                # Taller image
                img_width = page_width - 40
                img_height = img_width * aspect
            else:
                # Wider image
                img_height = page_height - 40
                img_width = img_height / aspect

            x = (page_width - img_width) / 2
            y = (page_height - img_height) / 2
            c.drawImage(
                ImageReader(img_buffer), x, y, width=img_width, height=img_height
            )
            c.showPage()

        c.save()
        return buffer.getvalue()
