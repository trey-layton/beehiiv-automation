import base64
import json
import logging
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


def generate_key() -> bytes:
    """
    Generates and returns a new encryption key.

    Returns:
        bytes: The generated encryption key.
    """
    return Fernet.generate_key()


def save_key(key: bytes, path: str) -> None:
    """
    Saves the encryption key to the specified path.

    Args:
        key (bytes): The encryption key.
        path (str): The file path to save the key.
    """
    try:
        with open(path, "wb") as key_file:
            key_file.write(key)
    except IOError as e:
        logging.error(f"Failed to save key to {path}: {e}")
        raise


def load_key(path: str) -> bytes:
    """
    Loads and returns the encryption key from the specified path.

    Args:
        path (str): The file path to load the key from.

    Returns:
        bytes: The loaded encryption key.

    Raises:
        FileNotFoundError: If the key file does not exist.
        IOError: If the key file cannot be read.
    """
    try:
        with open(path, "rb") as key_file:
            return key_file.read()
    except FileNotFoundError as e:
        logging.error(f"Key file not found at {path}: {e}")
        raise
    except IOError as e:
        logging.error(f"Failed to read key from {path}: {e}")
        raise


def encrypt_data(data: dict, key: bytes) -> str:
    """
    Encrypts the provided data using the encryption key and returns the base64 encoded string.

    Args:
        data (dict): The data to encrypt.
        key (bytes): The encryption key.

    Returns:
        str: The base64 encoded encrypted data.
    """
    fernet = Fernet(key)
    json_data = json.dumps(data).encode()
    encrypted_data = fernet.encrypt(json_data)
    return base64.urlsafe_b64encode(encrypted_data).decode()


def decrypt_data(encrypted_data: str, key: bytes) -> dict:
    """
    Decrypts the base64 encoded encrypted data using the encryption key and returns the original data.

    Args:
        encrypted_data (str): The data to decrypt, base64 encoded.
        key (bytes): The encryption key.

    Returns:
        dict: The decrypted data.

    Raises:
        ValueError: If decryption fails.
    """
    fernet = Fernet(key)
    try:
        # Ensure encrypted_data is a string before decoding
        if isinstance(encrypted_data, dict):
            encrypted_data = json.dumps(encrypted_data)
        logger.info(f"Type of encrypted_data before decoding: {type(encrypted_data)}")
        encrypted_data_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted_data = fernet.decrypt(encrypted_data_bytes)
        return json.loads(decrypted_data.decode())
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        raise ValueError(f"Decryption failed: {e}")
