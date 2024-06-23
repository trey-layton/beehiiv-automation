import sqlite3
import json
import os
import logging
from typing import Dict, Any
from core.encryption.encryption import encrypt_data, decrypt_data

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
DB_PATH = os.path.join(PROJECT_ROOT, "user_config.db")


def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            """CREATE TABLE IF NOT EXISTS users
                     (user_id TEXT PRIMARY KEY, encrypted_data BLOB)"""
        )
        conn.commit()
        logger.info("Database initialized successfully")
    except sqlite3.Error as e:
        logger.error(f"Error initializing database: {e}")
    finally:
        if conn:
            conn.close()


def save_user_config(user_config, key, user_id):
    conn = None
    try:
        logger.info(f"Saving user config for user {user_id}: {user_config}")
        encrypted_data = encrypt_data(json.dumps(user_config), key)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO users VALUES (?, ?)", (user_id, encrypted_data)
        )
        conn.commit()
        logger.info(f"User config saved for user {user_id}")

        # Verify the data was actually saved
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        if result:
            decrypted_data = decrypt_data(result[1], key)
            logger.info(
                f"Verified: Data for user {user_id} is in the database: {json.loads(decrypted_data)}"
            )
        else:
            logger.warning(
                f"Warning: Data for user {user_id} was not found in the database after saving"
            )

        return True
    except sqlite3.Error as e:
        logger.error(f"SQLite error when saving user config: {e}")
        return False
    except Exception as e:
        logger.error(f"Error saving user config: {e}")
        return False
    finally:
        if conn:
            conn.close()


def load_user_config(key: bytes, user_id: str) -> Dict[str, Any]:
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT encrypted_data FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        if result:
            encrypted_data = result[0]
            decrypted_data = decrypt_data(encrypted_data, key)
            user_config = json.loads(decrypted_data)
            logger.info(f"Successfully loaded and decrypted config for user {user_id}")
            logger.debug(f"Decrypted user config: {user_config}")
            return user_config
        else:
            logger.warning(f"No config found for user {user_id}")
            return None
    except Exception as e:
        logger.exception(f"Error loading user config for {user_id}:")
        return None
    finally:
        if conn:
            conn.close()


def update_user_config_field(user_id, field, value, key):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Fetch the current config
        c.execute("SELECT encrypted_data FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()

        if result:
            # Decrypt the current config
            decrypted_data = decrypt_data(result[0], key)
            user_config = json.loads(decrypted_data)

            # Update the specified field
            user_config[field] = value

            # Encrypt and save the updated config
            encrypted_data = encrypt_data(json.dumps(user_config), key)
            c.execute(
                "UPDATE users SET encrypted_data = ? WHERE user_id = ?",
                (encrypted_data, user_id),
            )
            conn.commit()

            logger.info(f"Updated {field} for user {user_id}")
            return True
        else:
            logger.warning(f"No config found for user {user_id}")
            return False
    except Exception as e:
        logger.error(f"Error updating user config field: {e}")
        return False
    finally:
        if conn:
            conn.close()


def update_twitter_tokens(user_id, new_access_key, new_access_secret, key):
    try:
        update_user_config_field(user_id, "twitter_access_key", new_access_key, key)
        update_user_config_field(
            user_id, "twitter_access_secret", new_access_secret, key
        )
        logger.info(f"Updated Twitter tokens for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error updating Twitter tokens: {e}")
        return False


def verify_and_update_twitter_tokens(user_id, key, verify_function, reauth_function):
    user_config = load_user_config(key, user_id)
    if not user_config:
        logger.error(f"No config found for user {user_id}")
        return False

    if verify_function(user_config):
        logger.info(f"Twitter tokens are valid for user {user_id}")
        return True
    else:
        logger.warning(
            f"Twitter tokens are invalid for user {user_id}. Attempting to reauthorize..."
        )
        new_tokens = reauth_function(user_id)
        if new_tokens:
            return update_twitter_tokens(
                user_id, new_tokens["access_key"], new_tokens["access_secret"], key
            )
        else:
            logger.error(f"Failed to reauthorize Twitter for user {user_id}")
            return False


# Initialize the database when this module is imported
init_db()
