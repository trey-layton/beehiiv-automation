# PostOnce Backend

A sophisticated content automation platform that transforms newsletter content (primarily from Beehiiv) into engaging social media posts for Twitter and LinkedIn using advanced AI processing.

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Poetry (recommended) or pip
- Supabase account
- Anthropic API key or OpenAI API key

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd postonce-backend
```

2. **Install dependencies**
```bash
# Using Poetry (recommended)
poetry install

# Using pip
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your actual values
```

4. **Run the application**
```bash
# Development
python run.py

# Production with Poetry
poetry run uvicorn api.main:app --host 0.0.0.0 --port 8000

# Production with pip
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## 🏗️ Architecture Overview

PostOnce follows a clean, layered architecture:

```
┌─────────────────┐
│   API Layer     │  FastAPI endpoints, authentication, streaming
├─────────────────┤
│ Business Logic  │  7-step AI processing pipeline
├─────────────────┤
│   Services      │  Account management, status tracking
├─────────────────┤
│   Data Layer    │  Supabase integration, models
└─────────────────┘
```

### Core Components

- **API Layer** (`api/`): FastAPI endpoints with JWT authentication
- **Core Processing** (`core/`): Main business logic and AI pipeline
- **LLM Steps** (`core/llm_steps/`): 7-step AI processing pipeline
- **Social Media** (`core/social_media/`): Platform-specific content generation
- **Services** (`core/services/`): Business services (accounts, status)
- **Models** (`core/models/`): Data structures and schemas
- **Utils** (`core/utils/`): Shared utilities and helpers

## 🤖 AI Processing Pipeline

PostOnce uses a sophisticated 7-step AI processing pipeline:

1. **Content Fetching**: Retrieve newsletter content from Beehiiv API
2. **Structure Analysis**: AI analyzes content structure and identifies sections
3. **Strategy Determination**: AI determines optimal posting strategy per section
4. **Content Generation**: Generate initial platform-specific content
5. **Image Relevance**: Check and incorporate relevant images
6. **Content Personalization**: Apply user's brand voice and style
7. **Hook Writing & Polishing**: Add engaging hooks and final optimization

Each step feeds into the next, building from raw newsletter content to platform-optimized social media posts.

## 📱 Supported Platforms & Content Types

### Twitter
- `precta_tweet`: Pre-newsletter announcements
- `postcta_tweet`: Post-newsletter CTAs
- `thread_tweet`: Multi-tweet threads
- `long_form_tweet`: Extended content tweets
- `carousel_tweet`: Visual carousel tweets (up to 4 slides)

### LinkedIn
- `long_form_post`: Professional long-form posts
- `carousel_post`: PDF carousel posts (up to 8 slides)
- `image_list`: Image-based posts

## 🔧 Configuration

### Required Environment Variables

```bash
# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# AI Providers (at least one required)
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key
LANGUAGE_MODEL_PROVIDER=anthropic  # or "openai"

# Optional Configuration
GUILD_ID=your_discord_guild_id
TWITTER_API_KEY=your_twitter_key
TWITTER_API_SECRET=your_twitter_secret
STACK_AUTH_API_URL=your_stack_auth_url
STACK_PROJECT_ID=your_stack_project_id
STACK_SECRET_SERVER_KEY=your_stack_server_key
```

### Optional Environment Variables

See `docs/CONFIGURATION.md` for complete configuration documentation.

## 📚 API Documentation

### Authentication
All endpoints require JWT authentication via Bearer token:
```bash
Authorization: Bearer <your_jwt_token>
```

### Main Endpoints

#### `POST /generate_content`
Generate social media content from newsletter content.

**Request Body:**
```json
{
  "account_id": "string",
  "content_id": "string",
  "post_id": "string (optional)",
  "content": "string (optional)",
  "content_type": "precta_tweet|postcta_tweet|thread_tweet|long_form_tweet|long_form_post|image_list|carousel_tweet|carousel_post"
}
```

**Response:** Server-Sent Events stream with real-time status updates

**Example:**
```bash
curl -X POST "https://your-api.com/generate_content" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "user123",
    "content_id": "content456",
    "post_id": "beehiiv_post_789",
    "content_type": "thread_tweet"
  }'
```

#### `GET /`
Health check endpoint.

**Response:**
```json
{
  "message": "PostOnce API is running"
}
```

For detailed API documentation, see `docs/API.md`.

## 🎨 Image Generation

PostOnce includes sophisticated image generation capabilities:

- **Carousel Generation**: Creates branded carousel images with custom styling
- **Brand Consistency**: Uses consistent colors, fonts, and layout
- **Platform Optimization**: Different formats for Twitter vs LinkedIn
- **Storage Integration**: Automatic upload to Supabase Storage

## 🚀 Deployment

### Vercel (Recommended)
PostOnce is optimized for Vercel deployment:

```json
{
  "version": 2,
  "functions": {
    "api/main.py": {
      "runtime": "@vercel/python@3.1.0",
      "memory": 1024,
      "maxDuration": 300
    }
  }
}
```

### Docker
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Manual Deployment
```bash
pip install -r requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## 🧪 Testing

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov-report=html

# Run specific test file
pytest tests/test_content_generation.py
```

### CLI Testing
```bash
python cli/main.py user_id "https://newsletter-url.com" --thread
```

## 🛠️ Development

### Project Structure
```
postonce-backend/
├── api/                    # FastAPI application
├── core/                   # Core business logic
│   ├── auth/              # Authentication
│   ├── config/            # Configuration management
│   ├── content/           # Content processing
│   ├── llm_steps/         # AI processing pipeline
│   ├── models/            # Data models
│   ├── services/          # Business services
│   ├── social_media/      # Platform integrations
│   └── utils/             # Shared utilities
├── cli/                   # Command line interface
├── docs/                  # Documentation
├── static/                # Static assets
└── tests/                 # Test files
```

### Code Style
- **Type hints**: All functions should include type hints
- **Docstrings**: All public functions must have docstrings
- **Logging**: Use structured logging throughout
- **Error handling**: Comprehensive error handling with proper HTTP status codes

### Adding New Content Types
1. Create new module in `core/social_media/platform/`
2. Define `instructions` dictionary with all required fields
3. Add to `CONTENT_TYPE_MAP` in relevant files
4. Add tests for new content type

## 📝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes and add tests
4. Ensure all tests pass: `pytest`
5. Submit a pull request

## 📄 License

[Your License Here]

## 🆘 Support

- **Documentation**: See `docs/` folder for detailed guides
- **Issues**: Create GitHub issues for bugs and feature requests
- **Discussions**: Use GitHub Discussions for questions

## 🔗 Related Projects

- PostOnce Frontend: [Link to frontend repo]
- PostOnce Mobile: [Link to mobile app] 