import base64
from cryptography.fernet import Fernet
import os
import logging

logger = logging.getLogger(__name__)


def get_key_path():
    PROJECT_ROOT = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    return os.path.join(PROJECT_ROOT, "core", "config", "secret.key")


KEY_PATH = get_key_path()


def load_key(key_path):
    with open(key_path, "rb") as key_file:
        return key_file.read()


def generate_key():
    return Fernet.generate_key()


def ensure_key_exists(key_path):
    if not os.path.exists(key_path):
        key = generate_key()
        os.makedirs(os.path.dirname(key_path), exist_ok=True)
        with open(key_path, "wb") as key_file:
            key_file.write(key)
        logger.info(f"New encryption key generated and saved to {key_path}")
    return load_key(key_path)


def encrypt_data(data, key):
    try:
        if isinstance(data, str):
            data = data.encode()
        f = Fernet(key)
        encrypted = f.encrypt(data)
        logger.debug(f"Encryption successful. First 20 bytes: {encrypted[:20]}")
        return encrypted
    except Exception as e:
        logger.error(f"Encryption failed: {str(e)}")
        logger.error(f"Key (first 10 bytes): {key[:10]}")
        logger.error(f"Key length: {len(key)}")
        raise


def decrypt_data(encrypted_data, key):
    try:
        logger.info(f"Type of encrypted_data before decoding: {type(encrypted_data)}")
        if isinstance(encrypted_data, str):
            encrypted_data = base64.b64decode(encrypted_data)
        f = Fernet(key)
        decrypted_data = f.decrypt(encrypted_data)
        logger.debug(f"Decryption successful. First 20 bytes: {decrypted_data[:20]}")
        return decrypted_data.decode()
    except Exception as e:
        logger.error(f"Decryption failed: {str(e)}")
        logger.error(f"Encrypted data (first 20 bytes): {encrypted_data[:20]}")
        logger.error(f"Key (first 10 bytes): {key[:10]}")
        logger.error(f"Key length: {len(key)}")
        raise


def get_key():
    key = ensure_key_exists(KEY_PATH)
    if len(key) != 32:
        key = base64.urlsafe_b64encode(key[:32])
    return key
