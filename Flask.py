from flask import Flask, request, redirect, session
import requests
import os
from dotenv import load_dotenv
from linkedin import get_linkedin_access_token, post_on_linkedin

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")
REDIRECT_URI = "https://martin-sweeping-optionally.ngrok-free.app/callback"  # Update with your ngrok URL


@app.route("/")
def home():
    return "Welcome to LinkedIn Integration"


@app.route("/login")
def login():
    auth_url = f"https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=r_liteprofile%20r_emailaddress%20w_member_social"
    return redirect(auth_url)


@app.route("/callback")
def callback():
    code = request.args.get("code")
    access_token = get_linkedin_access_token(code)
    if access_token:
        session["access_token"] = access_token
        return "Logged in successfully"
    else:
        return "Failed to obtain access token"


@app.route("/post_linkedin")
def post_linkedin():
    access_token = session.get("access_token")
    if not access_token:
        return redirect("/login")

    post_text = "Hello LinkedIn!"
    response = post_on_linkedin(access_token, post_text)
    return response


if __name__ == "__main__":
    app.run(port=80, debug=True)
