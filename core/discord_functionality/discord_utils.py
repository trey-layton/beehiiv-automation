import json
import logging
from typing import Dict, Any
from core.config.user_config import (
    save_user_config as db_save_user_config,
    load_user_config as db_load_user_config,
    DB_PATH,
)

logger = logging.getLogger(__name__)


def save_user_config(user_config: Dict[str, Any], key: bytes, user_id: str) -> None:
    """
    Saves the user configuration to the SQLite database.

    Args:
        user_config (Dict[str, Any]): The user configuration to save.
        key (bytes): The encryption key.
        user_id (str): The user ID for which to save the configuration.
    """
    try:
        db_save_user_config(user_config, key, user_id)
        logger.info(f"User configuration saved successfully for user {user_id}.")
    except Exception as e:
        logger.exception(f"Error saving user configuration for user {user_id}:")
        raise


def load_user_config(key: bytes, user_id: str) -> Dict[str, Any]:
    """
    Loads the user configuration from the SQLite database.

    Args:
        key (bytes): The encryption key.
        user_id (str): The user ID for which to load the configuration.

    Returns:
        Dict[str, Any]: The decrypted user configuration for the specified user.
    """
    try:
        user_config = db_load_user_config(key, user_id)
        if user_config is None:
            logger.warning(f"No configuration found for user ID: {user_id}")
            return {}
        logger.info(f"User configuration loaded successfully for user {user_id}.")
        return user_config
    except Exception as e:
        logger.exception(f"Error loading user configuration for user {user_id}:")
        raise


# You can remove the load_general_user_config function as it's no longer applicable
# with the new database structure. If you need to load all users, you'd need to
# implement a new function that queries all users from the database.

logger.info(f"Using database at: {DB_PATH}")
