# Configuration Guide

This document provides comprehensive information about configuring PostOnce Backend.

## Environment Variables

### Required Variables

#### Supabase Configuration
```bash
# Supabase project URL
SUPABASE_URL=https://your-project.supabase.co

# Service role key (not anon key!) for admin operations
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### AI Provider Configuration
You must configure at least one AI provider:

```bash
# Primary LLM provider (anthropic or openai)
LANGUAGE_MODEL_PROVIDER=anthropic

# Anthropic Claude API key
ANTHROPIC_API_KEY=sk-ant-api03-...

# OpenAI API key (alternative to Anthropic)
OPENAI_API_KEY=sk-...
```

### Optional Variables

#### Social Media Integration
```bash
# Twitter API credentials (for future Twitter posting features)
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret

# Discord integration (if using Discord notifications)
GUILD_ID=your_discord_guild_id
```

#### Authentication & Authorization
```bash
# Stack Auth configuration (if using Stack Auth instead of Supabase Auth)
STACK_AUTH_API_URL=https://api.stackauth.com
STACK_PROJECT_ID=your_stack_project_id
STACK_SECRET_SERVER_KEY=your_stack_server_key
```

## Configuration Files

### Environment Files
- `.env` - Production environment variables
- `.env.staging` - Staging environment variables (optional)
- `.env.example` - Template file with all available variables

### Application Configuration

#### Model Tiers
The application supports multiple AI model tiers for different use cases:

```python
MODEL_TIERS = {
    "high": {  # Best quality, slower, more expensive
        "anthropic": "claude-3-5-sonnet-20241022",
        "openai": "gpt-4o"
    },
    "medium": {  # Balanced quality and speed
        "anthropic": "claude-3-haiku-20240307", 
        "openai": "gpt-4o-mini"
    },
    "o1": {  # OpenAI's reasoning model
        "openai": "o1-preview"
    }
}
```

**Usage by Pipeline Step:**
- Structure Analysis: `o1` tier (requires reasoning)
- Content Generation: `o1` tier (complex generation)
- Personalization: `high` tier (quality important)
- Hook Writing: `high` tier (creative writing)
- AI Polish: `high` tier (final quality check)

#### Storage Configuration
Supabase storage buckets are automatically configured:

```python
BUCKET_CONFIGS = {
    "thumbnails": {
        "public": True,
        "allowedMimeTypes": ["image/*"],
        "fileSizeLimit": "5MB"
    },
    "carousels": {
        "public": True,
        "allowedMimeTypes": ["image/*", "application/pdf"],
        "fileSizeLimit": "2MB"
    }
}
```

## Database Schema

### Required Tables

#### `account_profiles`
Stores user account information and preferences:

```sql
CREATE TABLE account_profiles (
    account_id TEXT PRIMARY KEY,
    beehiiv_api_key TEXT NOT NULL,
    subscribe_url TEXT NOT NULL,
    publication_id TEXT NOT NULL,
    custom_prompt TEXT DEFAULT '',
    example_tweet TEXT DEFAULT '',
    example_linkedin TEXT DEFAULT '',
    newsletter_content TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### `content`
Tracks content generation status:

```sql
CREATE TABLE content (
    id TEXT PRIMARY KEY,
    account_id TEXT REFERENCES account_profiles(account_id),
    content_status TEXT DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Storage Buckets
- `thumbnails` - Newsletter thumbnail images
- `carousels` - Generated carousel images and PDFs

## Platform-Specific Configuration

### Beehiiv Integration
Each user account requires:
- `beehiiv_api_key` - API key from Beehiiv account
- `publication_id` - Publication ID from Beehiiv
- `subscribe_url` - Newsletter subscription URL

### Content Type Configuration
Each content type has specific parameters:

#### Twitter Content Types
- `precta_tweet` - 280 character limit, single tweet + reply
- `postcta_tweet` - 280 character limit, single tweet + reply  
- `thread_tweet` - Multiple tweets, 280 chars each
- `long_form_tweet` - Extended content format
- `carousel_tweet` - Up to 4 slides maximum

#### LinkedIn Content Types
- `long_form_post` - No character limit
- `carousel_post` - Up to 8 slides, PDF format
- `image_list` - Image-based posts

## Development Configuration

### Local Development
```bash
# Copy example environment file
cp .env.example .env

# Edit with your local values
nano .env

# Run development server
python run.py
```

### Testing Configuration
```bash
# Test database (optional separate Supabase project)
TEST_SUPABASE_URL=https://test-project.supabase.co
TEST_SUPABASE_SERVICE_ROLE_KEY=test_key

# Mock AI responses for testing
MOCK_AI_RESPONSES=true
```

## Production Configuration

### Vercel Deployment
Environment variables are set in Vercel dashboard:
1. Go to project settings
2. Add environment variables
3. Deploy

### Docker Configuration
```dockerfile
# Environment variables can be passed via:
# 1. .env file
# 2. Docker environment variables
# 3. Kubernetes secrets

ENV SUPABASE_URL=$SUPABASE_URL
ENV SUPABASE_SERVICE_ROLE_KEY=$SUPABASE_SERVICE_ROLE_KEY
# ... other variables
```

### Security Best Practices

#### API Keys
- Never commit API keys to version control
- Use environment variables or secure secret management
- Rotate keys regularly
- Use least-privilege access

#### Database Security
- Use service role key, not anon key for backend
- Enable Row Level Security (RLS) in Supabase
- Validate all inputs
- Use parameterized queries

#### Network Security
- Use HTTPS in production
- Configure CORS appropriately
- Implement rate limiting
- Monitor for unusual activity

## Monitoring & Logging

### Log Levels
```python
# Configure logging level
LOGGING_LEVEL=INFO

# Available levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Metrics Collection
```bash
# Optional metrics endpoints
ENABLE_METRICS=true
METRICS_PORT=9090
```

## Troubleshooting

### Common Issues

#### "Missing Supabase environment variables"
- Ensure `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are set
- Verify the service role key (not anon key)
- Check for trailing spaces in environment values

#### "Authentication failed"
- Verify JWT token is valid and not expired
- Check Supabase project settings
- Ensure proper CORS configuration

#### "AI API errors"
- Verify API keys are correct and have sufficient credits
- Check model availability and rate limits
- Monitor API usage quotas

#### "Storage bucket errors"
- Ensure buckets exist in Supabase
- Check storage permissions
- Verify file size limits

### Debug Mode
```bash
# Enable detailed logging
LOGGING_LEVEL=DEBUG

# Log AI requests/responses
LOG_AI_CALLS=true
```

## Configuration Validation

The application validates configuration on startup:

1. **Required variables check** - Fails if missing critical variables
2. **API connectivity test** - Tests Supabase and AI provider connections
3. **Storage initialization** - Creates required buckets if missing
4. **Database schema check** - Verifies required tables exist

Error messages will indicate specific configuration issues to resolve. 