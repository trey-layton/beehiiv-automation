from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Replace with your test user's email and password
response = supabase.auth.sign_in_with_password(
    {"email": "laytontrey3+1@gmail.com", "password": "35fwbf8d"}
)

print("Access Token:", response.session.access_token)
print("Refresh Token:", response.session.refresh_token)
