import base64
from cryptography.fernet import Fernet
import logging

logger = logging.getLogger(__name__)


def load_key(key_path):
    with open(key_path, "rb") as key_file:
        return key_file.read()


def generate_key():
    return Fernet.generate_key()


def encrypt_data(data, key):
    if isinstance(data, str):
        data = data.encode()
    f = Fernet(key)
    return f.encrypt(data)


def decrypt_data(encrypted_data, key):
    try:
        logger.info(f"Type of encrypted_data before decoding: {type(encrypted_data)}")
        if isinstance(encrypted_data, str):
            encrypted_data = base64.b64decode(encrypted_data)
        f = Fernet(key)
        decrypted_data = f.decrypt(encrypted_data)
        return decrypted_data.decode()
    except Exception as e:
        logger.error(f"Decryption failed: {str(e)}")
        return None
