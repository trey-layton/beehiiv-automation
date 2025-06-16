# Environment Setup Guide

This guide provides step-by-step instructions for setting up the PostOnce Backend environment.

## Environment Variables Template

Create a `.env` file in your project root with the following configuration:

```bash
# ============= REQUIRED CONFIGURATION =============

# Supabase Configuration (REQUIRED)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# AI Provider Configuration (AT LEAST ONE REQUIRED)
LANGUAGE_MODEL_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-api03-your-anthropic-key-here
OPENAI_API_KEY=sk-your-openai-key-here

# ============= OPTIONAL CONFIGURATION =============

# Social Media Integration (Optional)
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret

# Discord Integration (Optional)
GUILD_ID=your_discord_guild_id

# Stack Auth Integration (Optional - alternative to Supabase Auth)
STACK_AUTH_API_URL=https://api.stackauth.com
STACK_PROJECT_ID=your_stack_project_id
STACK_SECRET_SERVER_KEY=your_stack_server_key

# ============= DEVELOPMENT/DEBUG CONFIGURATION =============

# Logging Configuration
LOGGING_LEVEL=INFO
LOG_AI_CALLS=false

# Testing Configuration
MOCK_AI_RESPONSES=false
TEST_SUPABASE_URL=https://test-project.supabase.co
TEST_SUPABASE_SERVICE_ROLE_KEY=test_service_key

# Metrics and Monitoring (Optional)
ENABLE_METRICS=false
METRICS_PORT=9090
```

## Step-by-Step Setup

### 1. Supabase Setup

#### Create Supabase Project
1. Go to [https://supabase.com](https://supabase.com)
2. Sign up/Login and create a new project
3. Wait for project initialization (takes ~2 minutes)

#### Get API Credentials
1. Go to **Settings → API** in your Supabase dashboard
2. Copy the **URL** and **service_role secret** (NOT the anon key)
3. Add to your `.env` file:
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Create Database Tables
Execute this SQL in your Supabase SQL editor:

```sql
-- Account profiles table
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

-- Content tracking table
CREATE TABLE content (
    id TEXT PRIMARY KEY,
    account_id TEXT REFERENCES account_profiles(account_id),
    content_status TEXT DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_account_profiles_account_id ON account_profiles(account_id);
CREATE INDEX idx_content_account_id ON content(account_id);
CREATE INDEX idx_content_status ON content(content_status);
```

#### Configure Storage Buckets
Storage buckets are created automatically by the application, but you can create them manually:

1. Go to **Storage** in Supabase dashboard
2. Create bucket named `thumbnails` with public access
3. Create bucket named `carousels` with public access

### 2. AI Provider Setup

#### Option A: Anthropic (Recommended)
1. Go to [https://console.anthropic.com](https://console.anthropic.com)
2. Sign up and create an API key
3. Add to `.env`:
```bash
LANGUAGE_MODEL_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

#### Option B: OpenAI
1. Go to [https://platform.openai.com](https://platform.openai.com)
2. Create an API key
3. Add to `.env`:
```bash
LANGUAGE_MODEL_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
```

#### Option C: Both Providers
You can configure both for redundancy:
```bash
LANGUAGE_MODEL_PROVIDER=anthropic  # Primary provider
ANTHROPIC_API_KEY=sk-ant-api03-your-anthropic-key
OPENAI_API_KEY=sk-your-openai-key
```

### 3. Optional Integrations

#### Beehiiv API (Per User)
Each user needs their own Beehiiv credentials:
1. User logs into their Beehiiv account
2. Goes to Settings → API
3. Creates API key and gets publication ID
4. Enters in account profile via your frontend

#### Twitter API (Future Feature)
For direct Twitter posting (not currently implemented):
1. Apply for Twitter Developer account
2. Create a project and app
3. Get API key and secret
4. Add to `.env`

### 4. Development Setup

#### Install Dependencies
```bash
# Using Poetry (recommended)
poetry install

# Using pip
pip install -r requirements.txt
```

#### Verify Configuration
```bash
# Test environment variables
python -c "import os; print('Supabase URL:', os.getenv('SUPABASE_URL'))"

# Test Supabase connection
python -c "
from supabase import create_client
import os
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))
print('Supabase connection: OK')
"

# Test AI provider
python -c "
import os
from core.content.language_model_client import call_language_model
print('AI provider configured:', os.getenv('LANGUAGE_MODEL_PROVIDER'))
"
```

#### Run Application
```bash
# Development server
python run.py

# Production server
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### 5. Production Setup

#### Environment-Specific Configuration

**Staging Environment:**
```bash
# Create .env.staging
cp .env .env.staging

# Use staging Supabase project
SUPABASE_URL=https://staging-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=staging_service_key
```

**Production Environment:**
```bash
# Use production Supabase project
SUPABASE_URL=https://prod-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=prod_service_key

# Enable production logging
LOGGING_LEVEL=INFO
LOG_AI_CALLS=false

# Optional: Enable metrics
ENABLE_METRICS=true
METRICS_PORT=9090
```

#### Vercel Deployment
1. Connect your GitHub repo to Vercel
2. Add environment variables in Vercel dashboard:
   - Settings → Environment Variables
   - Add all required variables from `.env`
3. Deploy automatically on push to main branch

#### Docker Deployment
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

# Environment variables from secrets
ENV SUPABASE_URL=$SUPABASE_URL
ENV SUPABASE_SERVICE_ROLE_KEY=$SUPABASE_SERVICE_ROLE_KEY
ENV ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Security Configuration

### Best Practices

1. **Never commit `.env` files** to version control
2. **Use service role key**, not anon key for `SUPABASE_SERVICE_ROLE_KEY`
3. **Rotate API keys regularly** (quarterly recommended)
4. **Use environment-specific credentials** for staging/production
5. **Monitor API usage** and set up billing alerts

### Row Level Security (RLS)
Enable RLS in Supabase for additional security:

```sql
-- Enable RLS on tables
ALTER TABLE account_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE content ENABLE ROW LEVEL SECURITY;

-- Create policies (example - adjust based on your auth setup)
CREATE POLICY "Users can only access their own profiles" ON account_profiles
    FOR ALL USING (account_id = auth.uid()::text);

CREATE POLICY "Users can only access their own content" ON content
    FOR ALL USING (account_id = auth.uid()::text);
```

### API Rate Limiting
Consider adding rate limiting in production:

```python
# Install: pip install slowapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/generate_content")
@limiter.limit("10/minute")  # 10 requests per minute
async def generate_content_endpoint(...):
    # ... existing code
```

## Troubleshooting

### Common Issues

#### "Missing Supabase environment variables"
- Check `.env` file exists and has correct variables
- Verify no trailing spaces in environment values
- Ensure using service role key, not anon key

#### "Authentication failed" 
- Verify JWT token is valid and not expired
- Check Supabase project settings
- Ensure proper CORS configuration in Supabase

#### "AI API errors"
- Verify API keys are correct and have sufficient credits
- Check model availability and rate limits
- Monitor API usage quotas

#### "Storage bucket errors"
- Ensure buckets exist in Supabase Storage
- Check storage permissions and policies
- Verify file size limits

### Debug Mode
Enable detailed logging for troubleshooting:

```bash
LOGGING_LEVEL=DEBUG
LOG_AI_CALLS=true
```

### Health Checks
Test your setup with these endpoints:

```bash
# Health check
curl http://localhost:8000/

# Test authentication (replace with your JWT)
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:8000/generate_content \
     -d '{"account_id":"test","content_id":"test","content":"test","content_type":"precta_tweet"}'
```

## Monitoring Setup

### Application Monitoring
```bash
# Enable metrics collection
ENABLE_METRICS=true
METRICS_PORT=9090

# View metrics
curl http://localhost:9090/metrics
```

### Log Analysis
Configure structured logging for production monitoring:

```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.name
        })

# Apply to your loggers
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
```

This setup provides a robust foundation for running PostOnce Backend in any environment from development to production. 