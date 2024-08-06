BEEHIIV_PROJECT/
│
├── .vscode/
│   └── settings.json
│
├── api/
│   ├── get_token.py
│   └── main.py
│
├── cli/
│   └── main.py
│
├── core/
│   ├── auth/
│   │   ├── __init__.py
│   │   └── supabase_auth.py
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── environment.py
│   │   ├── feature_toggle.py
│   │   ├── feature_toggles.json
│   │   ├── secret.key
│   │   └── user_config.py
│   │
│   ├── content/
│   │   ├── __init__.py
│   │   ├── beehiiv_content.py
│   │   ├── content_extraction.py
│   │   ├── content_fetcher.py
│   │   ├── content_quality_check.py
│   │   ├── language_model_client.py
│   │   └── text_utils.py
│   │
│   ├── encryption/
│   │   ├── __init__.py
│   │   └── encryption.py
│   │
│   ├── models/
│   │   └── user.py
│   │
│   └── social_media/
│       ├── linkedin/
│       │   ├── generate_linkedin_post.py
│       │   └── testlinkedin.py
│       │
│       └── twitter/
│           ├── __init__.py
│           ├── generate_tweets.py
│           ├── media_upload.py
│           └── tweet_handler.py
│
├── js_utils/
│   └── twitter_text_util.js
│
├── tests/
│   ├── __init__.py
│   ├── mocks.py
│   └── test_api.py
│
├── .env
├── .env.staging
├── .gitignore
├── main_process.py
├── PROJECT_STRUCTURE.md
├── requirements.txt
└── vercel.json