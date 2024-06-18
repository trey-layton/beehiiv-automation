import os
import json
import logging
from typing import Optional, Dict, Any
from encryption.encryption import decrypt_data

logger = logging.getLogger(__name__)


def load_user_config(
    user_config_path: str, key: bytes, user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Loads and decrypts the user configuration.

    Args:
        user_config_path (str): The path to the encrypted user config file.
        key (bytes): The encryption key.
        user_id (Optional[str]): The user ID to fetch specific configuration.

    Returns:
        Dict[str, Any]: The decrypted user configuration.
    """
    if not os.path.exists(user_config_path):
        logger.error("user_config.enc file not found")
        return {}

    try:
        with open(user_config_path, "rb") as file:
            encrypted_data = json.loads(file.read().decode())
            logger.info(
                f"Encrypted data loaded: {json.dumps(encrypted_data, indent=4)}"
            )
    except (IOError, json.JSONDecodeError) as e:
        logger.exception("Failed to read or decode JSON from user_config.enc:")
        return {}

    if user_id:
        encrypted_user_config = encrypted_data.get(user_id)
        if not encrypted_user_config:
            logger.error(f"No configuration found for user {user_id}")
            return {}
        try:
            logger.info(
                f"Type of encrypted_user_config for user {user_id}: {type(encrypted_user_config)}"
            )
            if isinstance(encrypted_user_config, dict):
                encrypted_user_config = json.dumps(encrypted_user_config)
            user_config = decrypt_data(encrypted_user_config, key)
            return user_config
        except Exception as e:
            logger.exception(f"Failed to decrypt data for user {user_id}:")
            return {}
    else:
        user_config = {}
        for user, encrypted_config in encrypted_data.items():
            try:
                logger.info(f"Decrypting data for user: {user}")
                logger.info(
                    f"Type of encrypted_config for user {user}: {type(encrypted_config)}"
                )
                if isinstance(encrypted_config, dict):
                    encrypted_config = json.dumps(encrypted_config)
                decrypted_config = decrypt_data(encrypted_config, key)
                user_config[user] = decrypted_config
                logger.info(
                    f"Decrypted data for user {user}: {json.dumps(decrypted_config, indent=4)}"
                )
            except Exception as e:
                logger.exception(f"Failed to decrypt data for user {user}:")
                continue
        return user_config
