import json
import logging
import os
from typing import Dict, Any
from encryption.encryption import encrypt_data, decrypt_data

user_config_path = "user_config.enc"


def save_user_config(user_config: Dict[str, Dict[str, Any]], key: bytes) -> None:
    """
    Encrypts and saves the user configuration to a file.

    Args:
        user_config (Dict[str, Dict[str, Any]]): The user configuration to save.
        key (bytes): The encryption key.
    """
    try:
        encrypted_data = encrypt_data(user_config, key)
        with open(user_config_path, "w") as file:
            json.dump(encrypted_data, file)
        logging.info("User configuration saved successfully.")
    except Exception as e:
        logging.exception("Error saving user configuration:")
        raise


def load_user_config(user_config_path: str, key: bytes, user_id: str) -> Dict[str, Any]:
    """
    Loads and decrypts the user configuration from a file.

    Args:
        user_config_path (str): The path to the encrypted user configuration file.
        key (bytes): The encryption key.
        user_id (str): The user ID for which to load the configuration.

    Returns:
        Dict[str, Any]: The decrypted user configuration for the specified user.
    """
    try:
        if not os.path.exists(user_config_path):
            logging.error(f"{user_config_path} file not found.")
            return {}

        with open(user_config_path, "r") as file:
            encrypted_data = json.load(file)
        logging.info(f"Encrypted data loaded: {encrypted_data}")

        # Ensure the user ID format matches the keys in your configuration
        user_id_formatted = str(user_id)  # Adjust this based on your key format
        encrypted_user_config = encrypted_data.get(user_id_formatted)
        if not encrypted_user_config:
            raise ValueError(f"No configuration found for user ID: {user_id_formatted}")

        logging.info(
            f"Encrypted user config for {user_id_formatted}: {encrypted_user_config}"
        )
        user_config = decrypt_data(encrypted_user_config, key)
        logging.info(f"Decrypted data for user {user_id_formatted}: {user_config}")
        return user_config
    except Exception as e:
        logging.exception(f"Error loading user configuration for {user_id}:")
        raise


# Optionally, for completeness, you can keep the original function for general use:
def load_general_user_config(key: bytes) -> Dict[str, Dict[str, Any]]:
    """
    Loads and decrypts the entire user configuration from a file.

    Args:
        key (bytes): The encryption key.

    Returns:
        Dict[str, Dict[str, Any]]: The decrypted user configuration.
    """
    try:
        if not os.path.exists(user_config_path):
            logging.error(f"{user_config_path} file not found.")
            return {}

        with open(user_config_path, "r") as file:
            encrypted_data = json.load(file)
        user_config = decrypt_data(encrypted_data, key)
        logging.info("User configuration loaded successfully.")
        return user_config
    except Exception as e:
        logging.exception("Error loading user configuration:")
        raise
