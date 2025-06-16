"""
Constants and configuration values for PostOnce Backend.

This module centralizes all magic numbers, limits, and configuration
constants used throughout the application to improve maintainability
and prevent hardcoded values.
"""

from typing import Dict, Any

# ============= Content Generation Limits =============

# Character limits for different platforms
TWITTER_CHAR_LIMIT = 280
LINKEDIN_CHAR_LIMIT = None  # No limit for LinkedIn

# Slide limits for carousel content
TWITTER_MAX_SLIDES = 4
LINKEDIN_MAX_SLIDES = 8

# Content validation limits
MAX_HEADING_LENGTH = 50
MAX_SUBHEADING_LENGTH = 100
HEADING_TRUNCATE_SUFFIX = "..."
SUBHEADING_TRUNCATE_SUFFIX = "..."

# ============= Image Generation Settings =============

# Carousel image dimensions (width, height)
CAROUSEL_IMAGE_SIZE = (1200, 1500)

# Brand colors
PRIMARY_DARK_COLOR = "#2B3A4D"  # Dark blue background
TEXT_COLOR = "#FFFFFF"  # White text
ARROW_COLOR = "#FFFFFF"  # White arrows

# Font settings
DEFAULT_FONT_PATH = "./fonts/Lora-VariableFont_wght.ttf"
HEADING_FONT_SIZE = 96
SUBHEADING_FONT_SIZE = 48

# Arrow and spacing settings
ARROW_WIDTH = 3
ARROW_SIZE = (60, 30)
ARROW_MARGIN = 60
IMAGE_MARGIN = 100

# ============= API Configuration =============

# Timeout settings (in seconds)
LLM_API_TIMEOUT = 300  # 5 minutes
HTTP_REQUEST_TIMEOUT = 30

# Retry settings
MAX_RETRY_ATTEMPTS = 3
RETRY_MIN_WAIT = 4
RETRY_MAX_WAIT = 10

# Heartbeat interval for streaming (in seconds)
HEARTBEAT_INTERVAL = 5

# ============= Storage Configuration =============

# File size limits
THUMBNAIL_SIZE_LIMIT = "5MB"
CAROUSEL_SIZE_LIMIT = "2MB"

# Allowed MIME types
IMAGE_MIME_TYPES = ["image/*"]
PDF_MIME_TYPES = ["application/pdf"]

# Storage bucket names
THUMBNAILS_BUCKET = "thumbnails"
CAROUSELS_BUCKET = "carousels"

# Bucket configurations
BUCKET_CONFIGS: Dict[str, Dict[str, Any]] = {
    THUMBNAILS_BUCKET: {
        "public": True,
        "allowedMimeTypes": IMAGE_MIME_TYPES,
        "fileSizeLimit": THUMBNAIL_SIZE_LIMIT,
    },
    CAROUSELS_BUCKET: {
        "public": True,
        "allowedMimeTypes": IMAGE_MIME_TYPES + PDF_MIME_TYPES,
        "fileSizeLimit": CAROUSEL_SIZE_LIMIT,
    },
}

# ============= LLM Model Configuration =============

# Model tier configurations
MODEL_TIERS: Dict[str, Dict[str, Dict[str, Any]]] = {
    "high": {
        "anthropic": {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 200000,
            "max_output_tokens": 8192,
        },
        "openai": {
            "model": "gpt-4o",
            "max_tokens": 128000,
            "max_output_tokens": 4096,
        },
    },
    "medium": {
        "anthropic": {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 200000,
            "max_output_tokens": 4096,
        },
        "openai": {
            "model": "gpt-4o-mini",
            "max_tokens": 128000,
            "max_output_tokens": 4096,
        },
    },
    "o1": {
        "openai": {
            "model": "o1-preview",
            "max_tokens": 128000,
            "max_output_tokens": 4096,
        },
    },
}

# LLM generation settings
DEFAULT_TEMPERATURE = 0.5
HIGH_CREATIVITY_TEMPERATURE = 0.7

# ============= Content Processing Settings =============

# HTML cleaning settings - allowed tags for content processing
ALLOWED_HTML_TAGS = {
    "a",
    "b",
    "i",
    "u",
    "em",
    "strong",
    "img",
    "p",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "ul",
    "ol",
    "li",
}

# Content type mapping for social media platforms
CONTENT_TYPE_MAP: Dict[str, str] = {
    "precta_tweet": "core.social_media.twitter.precta_tweet",
    "postcta_tweet": "core.social_media.twitter.postcta_tweet",
    "thread_tweet": "core.social_media.twitter.thread_tweet",
    "long_form_tweet": "core.social_media.twitter.long_form_tweet",
    "long_form_post": "core.social_media.linkedin.long_form_post",
    "image_list": "core.social_media.image_list",
    "carousel_tweet": "core.social_media.twitter.carousel_tweet",
    "carousel_post": "core.social_media.linkedin.carousel_post",
}

# Content types that skip hook writing
CAROUSEL_CONTENT_TYPES = ["carousel_tweet", "carousel_post"]

# Content types by platform
TWITTER_CONTENT_TYPES = [
    "precta_tweet",
    "postcta_tweet",
    "thread_tweet",
    "long_form_tweet",
    "carousel_tweet",
]

LINKEDIN_CONTENT_TYPES = ["long_form_post", "carousel_post"]

# ============= Status and Error Messages =============

# Processing status messages
STATUS_MESSAGES = {
    "started": "Initializing content generation and editing",
    "analyzing": "Analyzing content structure",
    "analyzing_structure": "Breaking down content sections",
    "determining_strategy": "Planning content strategy",
    "generating": "Generating social media content",
    "writing_hooks": "Adding engaging hooks",
    "polishing": "Final content optimization",
    "generated": "Content generation complete",
    "failed": "Content generation failed",
    "heartbeat": "Still processing...",
}

# Error messages
ERROR_MESSAGES = {
    "missing_account": "Account profile not found",
    "validation_error": "Request validation failed",
    "auth_failed": "Authentication failed",
    "generation_failed": "Content generation failed",
    "invalid_content_type": "Invalid content type specified",
    "missing_instructions": "Missing content generation instructions",
    "llm_timeout": "AI processing timeout",
    "storage_error": "File storage operation failed",
}

# ============= Environment Variables =============

# Required environment variables
REQUIRED_ENV_VARS = ["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"]

# AI provider environment variables (at least one required)
AI_PROVIDER_ENV_VARS = ["ANTHROPIC_API_KEY", "OPENAI_API_KEY"]

# Optional environment variables
OPTIONAL_ENV_VARS = [
    "LANGUAGE_MODEL_PROVIDER",
    "GUILD_ID",
    "TWITTER_API_KEY",
    "TWITTER_API_SECRET",
    "STACK_AUTH_API_URL",
    "STACK_PROJECT_ID",
    "STACK_SECRET_SERVER_KEY",
]

# ============= Database Configuration =============

# Table names
ACCOUNT_PROFILES_TABLE = "account_profiles"
CONTENT_TABLE = "content"

# Default values
DEFAULT_CUSTOM_PROMPT = ""
DEFAULT_EXAMPLE_CONTENT = ""

# ============= File Processing Settings =============

# Image placeholder pattern for content processing
IMAGE_PLACEHOLDER_PATTERN = r"\[image:(.*?)\]"

# URL template patterns for replacement
URL_TEMPLATE_PATTERNS = {
    "subscribe_url": "{account_profile.subscribe_url}",
    "web_url": "{web_url}",
}

# Content delimiters for LLM responses
LLM_RESPONSE_DELIMITER_START = "~!"
LLM_RESPONSE_DELIMITER_END = "!~"

# ============= Deployment Settings =============

# Vercel configuration
VERCEL_MEMORY_LIMIT = 1024  # MB
VERCEL_MAX_DURATION = 300  # seconds (5 minutes)
VERCEL_PYTHON_RUNTIME = "@vercel/python@3.1.0"

# Default server settings
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_LOG_LEVEL = "info"
