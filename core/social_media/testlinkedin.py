import os
import requests
from requests_oauthlib import OAuth2Session
from dotenv import load_dotenv
import jwt

# Load environment variables
load_dotenv(dotenv_path="/Users/treylayton/Desktop/Coding/beehiiv_project/.env")

# LinkedIn OAuth2 settings
client_id = os.getenv("LINKEDIN_CLIENT_ID")
client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
redirect_uri = "https://martin-sweeping-optionally.ngrok-free.app/callback"  # Ensure this matches registered redirect URI
authorization_base_url = "https://www.linkedin.com/oauth/v2/authorization"
token_url = "https://www.linkedin.com/oauth/v2/accessToken"
userinfo_url = "https://api.linkedin.com/v2/userinfo"
jwks_uri = "https://www.linkedin.com/oauth/openid/jwks"
scope = ["openid", "profile", "email"]

# Debugging: Print client_id and client_secret to ensure they are loaded correctly
print("Client ID:", client_id)
print("Client Secret:", client_secret)

# Ensure client_id and client_secret are not None
if client_id is None or client_secret is None:
    raise ValueError(
        "Client ID or Client Secret is not set. Please check your .env file."
    )

# Step 1: User Authorization
linkedin = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scope)
authorization_url, state = linkedin.authorization_url(authorization_base_url)
print("Please go to %s and authorize access." % authorization_url)

# Get the authorization verifier code from the callback URL
redirect_response = input("Paste the full redirect URL here: ")

# Step 2: Fetch the access token and ID token
token = linkedin.fetch_token(
    token_url, client_secret=client_secret, authorization_response=redirect_response
)
access_token = token["access_token"]
id_token = token["id_token"]


# Step 3: Decode and validate the ID token
def decode_and_validate_id_token(id_token):
    # Fetch the public keys from LinkedIn
    response = requests.get(jwks_uri)
    jwks = response.json()
    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(jwks["keys"][0])

    # Decode and validate the ID token
    decoded_token = jwt.decode(
        id_token, public_key, algorithms=["RS256"], audience=client_id
    )
    return decoded_token


decoded_id_token = decode_and_validate_id_token(id_token)
print("Decoded ID Token:", decoded_id_token)


# Step 4: Fetch the user's profile information
def get_user_info(access_token):
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    response = requests.get(userinfo_url, headers=headers)

    if response.status_code != 200:
        raise Exception(
            f"Request returned an error: {response.status_code} {response.text}"
        )

    return response.json()


user_info = get_user_info(access_token)
print("User Info:", user_info)


# Step 5: Post content to LinkedIn
def post_linkedin(post_text, access_token, linkedin_member_id):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    payload = {
        "author": f"urn:li:person:{linkedin_member_id}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": post_text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }

    response = requests.post(
        "https://api.linkedin.com/v2/ugcPosts", headers=headers, json=payload
    )

    if response.status_code != 201:
        raise Exception(
            f"Request returned an error: {response.status_code} {response.text}"
        )

    print("LinkedIn post created successfully!")
    print("Response code:", response.status_code)


post_text = "This is a test post from my LinkedIn integration script."
linkedin_member_id = user_info["sub"]
post_linkedin(post_text, access_token, linkedin_member_id)
