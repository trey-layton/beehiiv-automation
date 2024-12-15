import io
import logging
import time
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any, List, Optional
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader

from core.utils.storage_utils import upload_to_supabase

logger = logging.getLogger(__name__)


class CarouselGenerator:
    def __init__(self, platform: str, font_path: Optional[str] = None):
        self.platform = platform
        self.max_slides = 8 if platform == "linkedin" else 4
        self.image_size = (1200, 1500)  # Updated size

        # Updated colors to match example
        self.primary_dark = "#2B3A4D"  # Dark blue background
        self.text_color = "#FFFFFF"  # White text

        # Use system fonts for fallback
        self.font_path = "/System/Library/Fonts/HelveticaNeue.ttc"  # For Mac
        # For Windows: "C:\\Windows\\Fonts\\segoeui.ttf"
        # For Linux: "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

        # Updated font sizes for new dimensions
        self.heading_size = 96
        self.subheading_size = 48

        # Arrow settings
        self.arrow_color = "#FFFFFF"
        self.arrow_width = 3  # Thinner line
        self.arrow_size = (60, 30)
        self.arrow_margin = 60

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

    def _create_arrow(self, draw: ImageDraw) -> None:
        """Draw a minimal arrow in bottom right corner"""
        width, height = self.image_size
        margin = self.arrow_margin

        # Calculate arrow position
        x1 = width - margin - self.arrow_size[0]
        x2 = width - margin
        y = height - margin

        # Draw arrow line and head with thinner stroke
        draw.line([(x1, y), (x2, y)], fill=self.arrow_color, width=self.arrow_width)
        draw.line(
            [(x2 - 20, y - 20), (x2, y), (x2 - 20, y + 20)],
            fill=self.arrow_color,
            width=self.arrow_width,
        )

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
        """Create a single slide with updated styling"""
        img = Image.new("RGB", self.image_size, self.primary_dark)
        draw = ImageDraw.Draw(img)

        # Load fonts
        try:
            heading_font = ImageFont.truetype(self.font_path, self.heading_size)
            subheading_font = ImageFont.truetype(self.font_path, self.subheading_size)
        except OSError:
            # Fallback to default system font if custom font fails
            heading_font = ImageFont.load_default()
            subheading_font = ImageFont.load_default()

        # Get text content
        heading = content.get("heading", "")
        subheading = content.get("subheading", "")

        # Calculate center position
        margin = 100
        available_width = self.image_size[0] - (2 * margin)

        # Center text vertically with better spacing
        total_height = 0
        heading_lines = self._wrap_text(heading, available_width, heading_font)
        heading_bbox = draw.multiline_textbbox((0, 0), heading_lines, font=heading_font)
        heading_height = heading_bbox[3] - heading_bbox[1]
        total_height += heading_height

        if subheading:
            subheading_lines = self._wrap_text(
                subheading, available_width, subheading_font
            )
            subheading_bbox = draw.multiline_textbbox(
                (0, 0), subheading_lines, font=subheading_font
            )
            subheading_height = subheading_bbox[3] - subheading_bbox[1]
            total_height += (
                subheading_height + 40
            )  # Space between heading and subheading

        # Calculate starting Y position to center content
        start_y = (self.image_size[1] - total_height) // 2

        # Draw heading
        x = (self.image_size[0] - available_width) // 2
        draw.multiline_text(
            (x, start_y),
            heading_lines,
            font=heading_font,
            fill=self.text_color,
            align="left",
        )

        # Draw subheading if present
        if subheading:
            draw.multiline_text(
                (x, start_y + heading_height + 40),
                subheading_lines,
                font=subheading_font,
                fill=self.text_color,
                align="left",
            )

        # Add arrow (except for last slide)
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

    async def generate_pdf_from_images(self, image_list: list[Image.Image]) -> bytes:
        """Convert a list of PIL Images into a single PDF."""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)

        for img in image_list:
            # Convert PIL image to bytes
            img_buffer = io.BytesIO()
            img.save(img_buffer, format="PNG")
            img_buffer.seek(0)

            # Add image to PDF, scaling to fit page while maintaining aspect ratio
            img_width, img_height = img.size
            aspect = img_height / float(img_width)

            # Use letter size page dimensions
            page_width = letter[0]
            page_height = letter[1]

            # Calculate dimensions to fit page
            if aspect > 1:
                # Image is taller than wide
                img_width = page_width - 40  # Leave 20pt margin on each side
                img_height = img_width * aspect
            else:
                # Image is wider than tall
                img_height = page_height - 40  # Leave 20pt margin on top and bottom
                img_width = img_height / aspect

            # Center image on page
            x = (page_width - img_width) / 2
            y = (page_height - img_height) / 2

            c.drawImage(
                ImageReader(img_buffer), x, y, width=img_width, height=img_height
            )
            c.showPage()

        c.save()
        return buffer.getvalue()
