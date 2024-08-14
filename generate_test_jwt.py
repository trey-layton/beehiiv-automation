import jwt
import datetime


def generate_test_jwt(user_id, secret_key):
    payload = {
        "aud": "authenticated",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1),
        "sub": user_id,
        "email": "bryony@futureofsex.com",
        "app_metadata": {"provider": "email"},
        "user_metadata": {},
        "role": "authenticated",
    }

    return jwt.encode(payload, secret_key, algorithm="HS256")


# Replace these with your actual values
user_id = "e19ebc89-0e95-4019-b34d-753880380df9"
secret_key = "y7OcZUYJtMFpAU74mOPMAKGxoiLLXHrXbNG4Ohvm8PCsLViHMS9fxqqhLRa/eodKzEJWnzF2vka1jK+t2UMmI7Q=="

token = generate_test_jwt(user_id, secret_key)
print(f"Generated JWT:\n{token}")
