# core/auth/supabase_auth.py
import os
from supabase import create_client, Client
import jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from core.models.account_profile import AccountProfile
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
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
