import os
from supabase import create_client, Client
import jwt
from fastapi import HTTPException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_ANON_KEY")
supabase: Client = create_client(supabase_url, supabase_key)


def verify_token(token: str):
    try:
        # Decode the JWT token
        decoded_token = jwt.decode(token, supabase_key, algorithms=["HS256"])

        # Check if the token is valid
        user = supabase.auth.get_user(token)

        if user and user.id == decoded_token.get("sub"):
            return user
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_user_id(token: str):
    user = verify_token(token)
    return user.id
