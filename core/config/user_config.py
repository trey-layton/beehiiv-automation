import sqlite3
import json
import os
import logging
from typing import Dict, Any
from core.encryption.encryption import encrypt_data, decrypt_data, get_key


logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
DB_PATH = os.path.join(PROJECT_ROOT, "user_config.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS users
                 (user_id TEXT PRIMARY KEY, encrypted_data BLOB)"""
    )
    conn.commit()
    conn.close()


def save_user_config(user_config, user_id):
    key = get_key()
    logger.info(f"Saving config for user: {user_id}")
    logger.info(f"Key (first 10 bytes): {key[:10]}")
    logger.info(f"Key length: {len(key)}")
    try:
        encrypted_data = encrypt_data(json.dumps(user_config).encode(), key)
        logger.info(f"Encrypted data (first 20 bytes): {encrypted_data[:20]}")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO users (user_id, encrypted_data) VALUES (?, ?)",
            (user_id, encrypted_data),
        )
        conn.commit()
        conn.close()
        logger.info(f"User config saved successfully for user: {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error saving user config: {str(e)}")
        return False


def load_user_config(user_id):
    key = get_key()
    logger.info(f"Loaded key (first 10 bytes): {key[:10]}")
    logger.info(f"Loaded key length: {len(key)}")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT encrypted_data FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    if result:
        try:
            logger.info(f"Encrypted data (first 20 bytes): {result[0][:20]}")
            decrypted_data = decrypt_data(result[0], key)
            return json.loads(decrypted_data)
        except Exception as e:
            logger.error(f"Error decrypting data for user {user_id}: {str(e)}")
            return None
    return None


def update_user_config_field(user_id, field, value):
    key = get_key()
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute("SELECT encrypted_data FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()

        if result:
            decrypted_data = decrypt_data(result[0], key)
            user_config = json.loads(decrypted_data)
            user_config[field] = value
            encrypted_data = encrypt_data(json.dumps(user_config).encode(), key)
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


def update_example_tweet(user_id, example_tweet):
    return update_user_config_field(user_id, "example_tweet", example_tweet)


def update_twitter_tokens(user_id, new_access_key, new_access_secret):
    try:
        user_config = load_user_config(user_id)
        if user_config is None:
            logger.error(f"No config found for user {user_id}")
            return False

        user_config["twitter_access_key"] = new_access_key
        user_config["twitter_access_secret"] = new_access_secret

        save_user_config(user_config, user_id)
        logger.info(f"Updated Twitter tokens for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error updating Twitter tokens: {e}")
        return False


def load_all_user_configs():
    key = get_key()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id, encrypted_data FROM users")
    results = c.fetchall()
    conn.close()

    all_configs = {}
    for user_id, encrypted_data in results:
        decrypted_data = decrypt_data(encrypted_data, key)
        all_configs[user_id] = json.loads(decrypted_data)

    return all_configs


# Initialize the database when this module is imported
init_db()
update_twitter_tokens = update_user_config_field
