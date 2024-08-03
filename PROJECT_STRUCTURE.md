# PostOnce Project Structure

```bash
BEEHIIV_PROJECT/
│
├── .vscode/
│   └── settings.json
│
├── cli/
│   └── main.py
│
├── cloud/
│
├── core/
│   ├── auth/
│   │   ├── __init__.py
│   │   └── stack_auth_client.py
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
│   │   ├── language_model_client.py
│   │   └── text_utils.py
│   │
│   ├── encryption/
│   │   ├── __init__.py
│   │   └── encryption.py
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
├── stack-auth-nextjs/
│
├── tests/
│   └── __init__.py
│
├── .env
├── .env.staging
├── .gitignore
├── manage_db.py
└── requirements.txt