import json
import logging
import sqlite3
from core.config.user_config import (
    get_key,
    init_db,
    DB_PATH,
    save_user_config,
    load_user_config,
)
from core.config.feature_toggle import feature_toggle
from core.encryption.encryption import decrypt_data, load_key, get_key_path
import os

logger = logging.getLogger(__name__)


async def reset_user_config(user_id: str) -> str:
    try:
        key = get_key()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT encrypted_data FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()

        if result:
            encrypted_data = result[0]
            decrypted_data = decrypt_data(encrypted_data, key)
            user_config = json.loads(decrypted_data)

            debug_info = f"User config for {user_id}:\n"
            for key, value in user_config.items():
                if key in [
                    "oauth_token",
                    "oauth_token_secret",
                    "twitter_access_key",
                    "twitter_access_secret",
                    "password",
                ]:
                    debug_info += f"{key}: {'*' * len(str(value))}\n"
                else:
                    debug_info += f"{key}: {value}\n"
            return debug_info
        else:
            return f"No configuration found for user {user_id}."
    except Exception as e:
        logger.exception(f"Error debugging user config for {user_id}:")
        return f"An error occurred while debugging the user configuration: {str(e)}"
    finally:
        if conn:
            conn.close()


async def delete_user(user_id: str) -> str:
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        if c.rowcount > 0:
            conn.commit()
            return f"User {user_id} deleted from the database"
        else:
            return f"User {user_id} not found in the database"
    except Exception as e:
        logger.exception(f"Error deleting user {user_id}:")
        return f"An error occurred while deleting the user: {str(e)}"
    finally:
        if conn:
            conn.close()


async def debug_user_config(user_id: str) -> str:
    try:
        key = get_key()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT encrypted_data FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()

        if result:
            encrypted_data = result[0]
            decrypted_data = decrypt_data(encrypted_data, key)
            user_config = json.loads(decrypted_data)

            debug_info = f"User config for {user_id}:\n"
            for key, value in user_config.items():
                if key in [
                    "oauth_token",
                    "oauth_token_secret",
                    "twitter_access_key",
                    "twitter_access_secret",
                    "password",
                ]:
                    debug_info += f"{key}: {'*' * len(str(value))}\n"
                else:
                    debug_info += f"{key}: {value}\n"
            return debug_info
        else:
            return f"No configuration found for user {user_id}."
    except Exception as e:
        logger.exception(f"Error debugging user config for {user_id}:")
        return f"An error occurred while debugging the user configuration: {str(e)}"
    finally:
        if conn:
            conn.close()


async def list_users() -> str:
    try:
        key = get_key()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT user_id, encrypted_data FROM users")
        results = c.fetchall()
        conn.close()

        if not results:
            return "No users found."

        user_list = "Registered users:\n"
        for user_id, encrypted_data in results:
            try:
                decrypted_data = decrypt_data(encrypted_data, key)
                if decrypted_data is not None:
                    user_data = json.loads(decrypted_data)
                    email = user_data.get("email", "No email")
                    user_list += f"User ID: {user_id} - Email: {email}\n"
                else:
                    user_list += f"User ID: {user_id} - Unable to decrypt data\n"
            except Exception as e:
                logger.error(f"Error decrypting data for user {user_id}: {str(e)}")
                user_list += f"User ID: {user_id} - Error: Unable to decrypt data\n"

        return user_list
    except Exception as e:
        logger.exception("Error listing users:")
        return f"An error occurred while listing users: {str(e)}"


def toggle_feature(feature_name: str, enable: bool) -> str:
    if enable:
        feature_toggle.enable_feature(feature_name)
    else:
        feature_toggle.disable_feature(feature_name)
    return f"Feature '{feature_name}' has been {'enabled' if enable else 'disabled'}."


def list_features() -> str:
    return "\n".join(
        [
            f"{feature}: {'Enabled' if enabled else 'Disabled'}"
            for feature, enabled in feature_toggle.toggles.items()
        ]
    )


async def debug_encryption_key() -> str:
    try:
        key = get_key()
        if key:
            return f"Encryption key loaded successfully. Key length: {len(key)}"
        else:
            return "Failed to load encryption key."
    except Exception as e:
        logger.error(f"Error in debug_encryption_key: {str(e)}")
        return f"An error occurred: {str(e)}"
