import os
import requests
from requests_oauthlib import OAuth2Session
from flask import Flask, request, redirect, session, url_for
from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Replace with your actual secret key

# Load environment variables
load_dotenv(dotenv_path="/Users/treylayton/Desktop/Coding/beehiiv_project/.env")

# LinkedIn OAuth2 settings
client_id = os.getenv("LINKEDIN_CLIENT_ID")
client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
redirect_uri = "https://martin-sweeping-optionally.ngrok-free.app/callback"
authorization_base_url = "https://www.linkedin.com/oauth/v2/authorization"
token_url = "https://www.linkedin.com/oauth/v2/accessToken"
userinfo_url = "https://api.linkedin.com/v2/userinfo"
scope = ["openid", "profile", "email"]


@app.route("/")
def index():
    return "Welcome to the LinkedIn OAuth2 Test App!"


@app.route("/login")
def login():
    linkedin = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scope)
    authorization_url, state = linkedin.authorization_url(authorization_base_url)
    session["oauth_state"] = state
    return redirect(authorization_url)


@app.route("/callback")
def callback():
    linkedin = OAuth2Session(
        client_id, state=session["oauth_state"], redirect_uri=redirect_uri
    )
    token = linkedin.fetch_token(
        token_url, client_secret=client_secret, authorization_response=request.url
    )
    session["oauth_token"] = token
    return redirect(url_for(".profile"))


@app.route("/profile")
def profile():
    linkedin = OAuth2Session(client_id, token=session["oauth_token"])
    response = linkedin.get(userinfo_url)
    return response.json()


if __name__ == "__main__":
    app.run(port=5000, debug=True)
