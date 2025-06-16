# API Documentation

This document provides comprehensive API documentation for PostOnce Backend.

## Base URL
```
Production: https://your-domain.vercel.app
Development: http://localhost:8000
```

## Authentication

All API endpoints (except health check) require JWT authentication via Bearer token:

```http
Authorization: Bearer <your_jwt_token>
```

### Getting a JWT Token
Tokens are obtained through Supabase authentication. Use the Supabase client to authenticate:

```javascript
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password123'
})
const token = data.session.access_token
```

## Endpoints

### Health Check

#### `GET /`
Check if the API is running.

**Response:**
```json
{
  "message": "PostOnce API is running"
}
```

**Example:**
```bash
curl https://your-api.com/
```

---

### Content Generation

#### `POST /generate_content`
Generate social media content from newsletter content.

This endpoint processes newsletter content through the AI pipeline and returns a Server-Sent Events stream with real-time status updates.

**Headers:**
```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "account_id": "string",      // Required: User account identifier
  "content_id": "string",      // Required: Unique content generation ID
  "post_id": "string",         // Optional: Beehiiv post ID (mutually exclusive with content)
  "content": "string",         // Optional: Direct content input (mutually exclusive with post_id)
  "content_type": "string"     // Required: Type of content to generate
}
```

**Content Types:**
- `precta_tweet` - Pre-newsletter announcement tweet
- `postcta_tweet` - Post-newsletter CTA tweet
- `thread_tweet` - Multi-tweet thread
- `long_form_tweet` - Extended tweet content
- `long_form_post` - LinkedIn long-form post
- `image_list` - Image-based social media post
- `carousel_tweet` - Twitter carousel (up to 4 slides)
- `carousel_post` - LinkedIn carousel (up to 8 slides)

**Response:**
Server-Sent Events stream with status updates:

```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

**Status Events:**
```json
{"status": "started", "message": "Initializing content generation"}
{"status": "analyzing", "message": "Analyzing content structure"}
{"status": "analyzing_structure", "message": "Breaking down content sections"}
{"status": "determining_strategy", "message": "Planning content strategy"}
{"status": "generating", "message": "Generating social media content"}
{"status": "writing_hooks", "message": "Adding engaging hooks"}
{"status": "polishing", "message": "Final content optimization"}
{"status": "generated", "message": "Content generation complete", "data": {...}}
{"status": "heartbeat", "message": "Still processing..."}
```

**Success Response Data:**
```json
{
  "provider": "twitter|linkedin",
  "type": "precta_tweet",
  "content": [
    {
      "post_number": 1,
      "post_content": [
        {
          "post_type": "main_tweet",
          "post_content": "Tweet content here",
          "images": ["https://image-url.com"] // Optional
        },
        {
          "post_type": "reply_tweet", 
          "post_content": "Reply content here"
        }
      ]
    }
  ],
  "thumbnail_url": "https://thumbnail-url.com",
  "metadata": {
    "web_url": "https://newsletter-url.com",
    "post_id": "beehiiv_post_id"
  },
  "success": true
}
```

**Error Response:**
```json
{
  "status": "failed",
  "error": "Error description",
  "success": false
}
```

**Examples:**

1. **Generate from Beehiiv post:**
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

2. **Generate from direct content:**
```bash
curl -X POST "https://your-api.com/generate_content" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "user123",
    "content_id": "content456",
    "content": "Your newsletter content here...",
    "content_type": "long_form_post"
  }'
```

3. **JavaScript Example:**
```javascript
const response = await fetch('/generate_content', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    account_id: 'user123',
    content_id: 'content456',
    post_id: 'beehiiv_post_789',
    content_type: 'precta_tweet'
  })
});

// Handle Server-Sent Events
const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');
  
  for (const line of lines) {
    if (line.trim()) {
      try {
        const data = JSON.parse(line);
        console.log('Status:', data.status);
        
        if (data.status === 'generated') {
          console.log('Final content:', data.data);
        }
      } catch (e) {
        console.log('Raw message:', line);
      }
    }
  }
}
```

## Content Type Specifications

### Twitter Content Types

#### `precta_tweet`
Pre-newsletter announcement tweet.

**Structure:**
```json
{
  "content_type": "precta_tweet",
  "content_container": [
    {
      "post_type": "main_tweet",
      "post_content": "Teaser content (280 chars max)",
      "images": ["url"] // Optional
    },
    {
      "post_type": "reply_tweet",
      "post_content": "Subscribe CTA with link"
    }
  ]
}
```

#### `thread_tweet` 
Multi-tweet thread.

**Structure:**
```json
{
  "content_type": "thread_tweet",
  "content_container": [
    {
      "post_type": "thread_tweet",
      "post_content": "First tweet (280 chars max)",
      "images": ["url"] // Optional
    },
    {
      "post_type": "thread_tweet", 
      "post_content": "Second tweet (280 chars max)"
    }
    // ... more tweets
  ]
}
```

#### `carousel_tweet`
Visual carousel tweet (up to 4 slides).

**Structure:**
```json
{
  "content_type": "carousel_tweet",
  "content_container": [
    {
      "heading": "Slide 1 title",
      "subheading": "Optional subtitle"
    },
    {
      "heading": "Slide 2 title", 
      "subheading": "Optional subtitle"
    }
    // ... up to 4 slides
  ]
}
```

### LinkedIn Content Types

#### `long_form_post`
Professional long-form LinkedIn post.

**Structure:**
```json
{
  "content_type": "long_form_post",
  "content_container": [
    {
      "post_type": "linkedin_post",
      "post_content": "Full post content (no length limit)",
      "images": ["url"] // Optional
    }
  ]
}
```

#### `carousel_post` 
LinkedIn PDF carousel (up to 8 slides).

**Structure:**
```json
{
  "content_type": "carousel_post",
  "content_container": [
    {
      "heading": "Slide 1 title",
      "subheading": "Optional subtitle"
    }
    // ... up to 8 slides
  ]
}
```

## Error Handling

### HTTP Status Codes

- `200` - Success (for health check)
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (invalid/missing JWT token)
- `404` - Not Found (account profile not found)
- `500` - Internal Server Error

### Error Response Format

```json
{
  "detail": "Error description",
  "error_code": "SPECIFIC_ERROR_CODE", // Optional
  "success": false
}
```

### Common Errors

#### Authentication Errors
```json
{
  "detail": "Failed to authenticate",
  "error_code": "AUTH_FAILED"
}
```

#### Validation Errors
```json
{
  "detail": "Exactly one of post_id or content must be provided",
  "error_code": "VALIDATION_ERROR"
}
```

#### Account Not Found
```json
{
  "detail": "Account profile not found", 
  "error_code": "ACCOUNT_NOT_FOUND"
}
```

#### Content Generation Errors
```json
{
  "detail": "Failed to generate content",
  "error_code": "GENERATION_FAILED"
}
```

## Rate Limiting

Currently no rate limiting is implemented, but recommended limits for production:

- **Content Generation**: 10 requests per minute per account
- **Health Check**: 100 requests per minute per IP

## Request/Response Examples

### Complete Workflow Example

1. **Authenticate with Supabase**
2. **Generate content**
3. **Handle streaming response**

```javascript
// 1. Authenticate
const { data: authData } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password123'
});

const token = authData.session.access_token;

// 2. Generate content
const response = await fetch('/generate_content', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    account_id: 'user123',
    content_id: `content_${Date.now()}`,
    post_id: 'beehiiv_post_id',
    content_type: 'thread_tweet'
  })
});

// 3. Handle streaming response  
const reader = response.body.getReader();
let finalContent = null;

try {
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = new TextDecoder().decode(value);
    const lines = chunk.split('\n').filter(line => line.trim());
    
    for (const line of lines) {
      try {
        const event = JSON.parse(line);
        
        switch (event.status) {
          case 'started':
          case 'analyzing':
          case 'generating':
            console.log('Status:', event.message);
            break;
          case 'generated':
            finalContent = event.data;
            console.log('Generated content:', finalContent);
            break;
          case 'failed':
            throw new Error(event.error);
        }
      } catch (parseError) {
        console.log('Non-JSON message:', line);
      }
    }
  }
} finally {
  reader.releaseLock();
}

// Use finalContent for your application
if (finalContent) {
  // Process the generated social media content
  finalContent.content.forEach(post => {
    console.log(`Post ${post.post_number}:`, post.post_content);
  });
}
```

## WebSocket Alternative

For applications that prefer WebSocket over Server-Sent Events, a WebSocket endpoint may be added in future versions. The current SSE implementation provides the same real-time capabilities with broader browser support. 