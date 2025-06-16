# AI Processing Pipeline Documentation

PostOnce uses a sophisticated 7-step AI processing pipeline to transform newsletter content into optimized social media posts. Each step builds upon the previous, creating a comprehensive content generation and optimization system.

## Pipeline Overview

```
Raw Newsletter Content
         ↓
1. Structure Analysis     ← AI identifies content sections
         ↓
2. Strategy Determination ← AI plans posting strategy  
         ↓
3. Content Generation     ← AI creates platform-specific content
         ↓
4. Image Relevance       ← AI checks image applicability
         ↓
5. Personalization       ← AI applies brand voice
         ↓
6. Hook Writing          ← AI adds engaging elements
         ↓
7. Final Polish          ← AI optimizes and finalizes
         ↓
Optimized Social Media Posts
```

## Step-by-Step Breakdown

### Step 1: Structure Analysis (`structure_analysis.py`)

**Purpose**: Break down newsletter content into logical, processable sections.

**AI Model**: OpenAI o1-preview (reasoning model)
**Input**: Raw newsletter content (HTML-cleaned)
**Output**: Structured JSON with content sections

**Process**:
- Identifies main stories vs. secondary content
- Groups related articles into meaningful sections
- Filters out promotional/advertising content
- Creates descriptive section titles
- Preserves image placeholders and URLs

**Example Output**:
```json
{
  "sections": [
    {
      "section_title": "Main Story",
      "section_content": "In-depth article content..."
    },
    {
      "section_title": "Headlines",
      "section_content": "Brief news items and updates..."
    }
  ]
}
```

**Key Features**:
- Intelligent sectioning based on content themes
- Promotional content filtering
- Edge case handling (interrupted content, mixed formats)
- Robust JSON parsing with fallback mechanisms

---

### Step 2: Strategy Determination (`content_strategy.py`)

**Purpose**: Plan optimal social media posting strategy for each content section.

**AI Model**: OpenAI o1-preview (reasoning model)
**Input**: Structured sections from Step 1
**Output**: Strategy array with posting recommendations

**Process**:
- Analyzes each section for social media potential
- Determines optimal content type and approach
- Plans content distribution across multiple posts
- Assigns priority and posting sequence

**Example Output**:
```json
[
  {
    "post_number": 1,
    "section_title": "Main Story",
    "section_content": "Content for main story...",
    "strategy": "Create engaging thread to break down complex topic",
    "priority": "high"
  },
  {
    "post_number": 2, 
    "section_title": "Headlines",
    "section_content": "Quick updates...",
    "strategy": "Single impactful post highlighting key points",
    "priority": "medium"
  }
]
```

**Strategic Considerations**:
- Content complexity and depth
- Audience engagement potential
- Platform-specific optimization
- Posting sequence and timing

---

### Step 3: Content Generation (`content_generator.py`)

**Purpose**: Generate initial platform-specific social media content.

**AI Model**: OpenAI o1-preview (complex generation)
**Input**: Strategy array from Step 2 + content type + account profile
**Output**: Platform-formatted content ready for personalization

**Process**:
- Creates platform-specific content formats
- Applies content type requirements (character limits, structure)
- Incorporates user's subscribe URL and web links
- Validates content structure and formatting

**Content Types Supported**:

#### Twitter:
- `precta_tweet`: Pre-newsletter announcements (280 chars)
- `postcta_tweet`: Post-newsletter CTAs (280 chars)
- `thread_tweet`: Multi-tweet threads (280 chars each)
- `long_form_tweet`: Extended content format
- `carousel_tweet`: Visual carousels (4 slides max)

#### LinkedIn:
- `long_form_post`: Professional posts (no limit)
- `carousel_post`: PDF carousels (8 slides max)

**Example Output**:
```json
{
  "content_type": "thread_tweet",
  "content_container": [
    {
      "post_type": "thread_tweet",
      "post_content": "🧵 Thread about the major industry changes... (1/3)"
    },
    {
      "post_type": "thread_tweet", 
      "post_content": "The implications are significant because... (2/3)"
    },
    {
      "post_type": "thread_tweet",
      "post_content": "What this means for you: ... (3/3)"
    }
  ]
}
```

---

### Step 4: Image Relevance (`image_relevance.py`)

**Purpose**: Analyze image relevance and incorporate applicable images.

**AI Model**: Claude 3.5 Sonnet (high tier)
**Input**: Generated content + extracted image URLs
**Output**: Content with relevant images incorporated

**Process**:
- Analyzes image-content relevance using AI
- Determines which images enhance the social media post
- Incorporates relevant images into content structure
- Handles different image formats and sources

**Image Processing**:
- Extracts images from newsletter content
- Analyzes relevance to specific content sections
- Incorporates images into appropriate content formats
- Maintains image URLs for final rendering

**Example Integration**:
```json
{
  "post_type": "main_tweet",
  "post_content": "Amazing breakthrough in AI technology...",
  "images": ["https://newsletter.com/ai-breakthrough.jpg"]
}
```

---

### Step 5: Content Personalization (`content_personalization.py`)

**Purpose**: Apply user's unique brand voice and writing style.

**AI Model**: Claude 3.5 Sonnet (high tier)
**Input**: Generated content + user's style examples
**Output**: Personalized content matching user's voice

**Process**:
- Analyzes user's writing style from examples
- Applies tone, vocabulary, and structure patterns
- Maintains original message while matching voice
- Preserves platform requirements and constraints

**Style Analysis Elements**:
- Tone (formal, casual, humorous)
- Vocabulary and language complexity
- Sentence structure and length
- Punctuation and capitalization preferences
- Use of emojis, hashtags, and styling tools
- Personal anecdotes and rhetorical devices

**Personalization Sources**:
- `example_tweet`: User's Twitter style examples
- `example_linkedin`: User's LinkedIn style examples
- `newsletter_content`: User's newsletter writing style (fallback)

---

### Step 6: Hook Writing (`hook_writer.py`)

**Purpose**: Add engaging hooks, openings, and calls-to-action.

**AI Model**: Claude 3.5 Sonnet (high tier)
**Input**: Personalized content + content type instructions
**Output**: Content with compelling hooks and CTAs

**Process**:
- Analyzes content for hook opportunities
- Creates platform-specific engaging openings
- Adds compelling calls-to-action
- Optimizes for engagement and click-through

**Hook Types**:
- **Question hooks**: Engage with curiosity
- **Statistic hooks**: Lead with compelling data
- **Story hooks**: Personal anecdotes and narratives
- **Controversy hooks**: Thought-provoking statements
- **Benefit hooks**: Clear value propositions

**CTA Integration**:
- Newsletter subscription prompts
- Content engagement requests
- Link sharing encouragement
- Follow-up action guidance

**Note**: Carousel content types skip this step as hooks are handled differently in visual formats.

---

### Step 7: AI Polish (`ai_polisher.py`)

**Purpose**: Final optimization and quality assurance.

**AI Model**: Claude 3.5 Sonnet (high tier)
**Input**: Content with hooks + content type instructions
**Output**: Final polished content ready for posting

**Process**:
- Final quality check and optimization
- Grammar and style refinement
- Platform requirement validation
- Engagement optimization

**Polish Elements**:
- Grammar and syntax correction
- Flow and readability improvement
- Platform-specific optimization
- Character limit compliance
- Hashtag and mention optimization
- Final engagement enhancement

**Quality Checks**:
- Content coherence and clarity
- Brand voice consistency
- Platform requirement adherence
- Link and image validation
- CTA effectiveness

## Pipeline Configuration

### Model Tier Usage

```python
PIPELINE_MODEL_TIERS = {
    "structure_analysis": "o1",      # Requires advanced reasoning
    "content_strategy": "o1",        # Complex strategic thinking
    "content_generation": "o1",      # Sophisticated content creation
    "image_relevance": "high",       # Quality image analysis
    "personalization": "high",       # Important voice matching
    "hook_writing": "high",          # Creative writing quality
    "ai_polish": "high"              # Final quality assurance
}
```

### Error Handling

Each step includes comprehensive error handling:
- Graceful fallbacks for AI failures
- Validation of output formats
- Logging for debugging and monitoring
- Status updates for real-time feedback

### Performance Optimization

- Async processing throughout pipeline
- Intelligent model tier selection
- Retry logic with exponential backoff
- Caching where appropriate

## Status Tracking

The pipeline provides real-time status updates:

```
analyzing → analyzing_structure → determining_strategy → generating → 
writing_hooks → polishing → generated
```

Each status update includes:
- Current step description
- Progress indicators
- Error details (if applicable)
- Completion status

## Integration Points

### Input Sources
- Beehiiv API content
- Direct content input
- Account profile data
- User style examples

### Output Formats
- Platform-specific JSON structures
- Image URL references
- Metadata preservation
- Success/error indicators

### External Dependencies
- Supabase for data storage
- AI provider APIs (Anthropic/OpenAI)
- Image storage and processing
- Status tracking system

## Monitoring and Analytics

### Key Metrics
- Processing time per step
- Success/failure rates
- Content quality scores
- User engagement correlation

### Logging
- Detailed step-by-step logging
- Error tracking and analysis
- Performance monitoring
- User behavior insights

### Debugging
- Step-by-step content inspection
- AI response analysis
- Error reproduction and fixing
- Quality assurance testing

This pipeline represents a sophisticated approach to automated content creation that maintains quality, personalization, and engagement while scaling efficiently across multiple users and content types. 