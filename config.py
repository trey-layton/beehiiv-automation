import os
import logging
from dotenv import load_dotenv
from cryptography.fernet import Fernet
import base64
import json

# Load environment variables from .env file
load_dotenv(dotenv_path="/root/beehiiv-automation/.env")

logger = logging.getLogger(__name__)


def load_key():
    return open("secret.key", "rb").read()


def decrypt_data(encrypted_data, key):
    cipher_suite = Fernet(key)
    encrypted_data = base64.b64decode(encrypted_data)  # Decode base64 to bytes
    decrypted_data = cipher_suite.decrypt(encrypted_data)
    return json.loads(decrypted_data.decode())


def load_user_config():
    if not os.path.exists("user_config.enc"):
        logger.info("user_config.enc file not found")
        return {}

    with open("user_config.enc", "rb") as file:
        try:
            encrypted_data = json.loads(file.read().decode())
            logger.info(
                f"Encrypted data loaded: {json.dumps(encrypted_data, indent=4)}"
            )
        except json.JSONDecodeError as e:
            logger.exception("Failed to decode JSON from user_config.enc:")
            return {}

    user_config = {}
    for user, encrypted_config in encrypted_data.items():
        try:
            logger.info(f"Decrypting data for user: {user}")
            key = load_key()
            decrypted_config = decrypt_data(encrypted_config.encode(), key)
            user_config[user] = decrypted_config
            logger.info(
                f"Decrypted data for user {user}: {json.dumps(decrypted_config, indent=4)}"
            )
        except Exception as e:
            logger.exception(f"Failed to decrypt data for user {user}:")
            continue

    return user_config


def get_config(user_id, override_config=None):
    if override_config:
        return override_config

    # Load environment variables
    env_config = {
        "twitter_api_key": os.getenv("TWITTER_API_KEY"),
        "twitter_api_secret": os.getenv("TWITTER_API_SECRET"),
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
    }

    # Verify that critical environment variables are set
    for key, value in env_config.items():
        if value is None:
            logger.error(f"Environment variable {key.upper()} is not set.")
        else:
            logger.info(f"{key.upper()} is set to: {value}")

    # Load and decrypt user-specific configuration
    user_config = load_user_config().get(user_id, {})

    # Combine both configurations
    config = {
        **env_config,
        "twitter_access_key": user_config.get("twitter_access_key"),
        "twitter_access_secret": user_config.get("twitter_access_secret"),
        "beehiiv_api_key": user_config.get("beehiiv_api_key"),
        "subscribe_url": user_config.get("subscribe_url"),
        "publication_id": user_config.get("publication_id"),
    }

    # Log combined configuration
    for key, value in config.items():
        if value is None:
            logger.error(f"Configuration variable {key} is not set.")
        else:
            logger.info(f"Configuration variable {key} is set to: {value}")

    logger.debug(f"Final config dictionary: {config}")

    return config


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    user_id = "treylayton.eth"  # Replace with actual user_id you want to test
    config = get_config(user_id)
    logger.info(f"Loaded configuration: {config}")
