import hashlib
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import base64

KEY_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'encryption_key.key')

def _get_or_create_key() -> bytes:
    if not os.path.exists(os.path.dirname(KEY_FILE)):
        os.makedirs(os.path.dirname(KEY_FILE), exist_ok=True)
    
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, 'rb') as f:
            return f.read()
    
    key = Fernet.generate_key()
    with open(KEY_FILE, 'wb') as f:
        f.write(key)
    return key

def encrypt_data(data: str) -> str:
    key = _get_or_create_key()
    f = Fernet(key)
    return f.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    key = _get_or_create_key()
    f = Fernet(key)
    return f.decrypt(encrypted_data.encode()).decode()

def hash_id_card(id_card: str) -> str:
    if not id_card:
        return ""
    return hashlib.sha256(id_card.strip().encode()).hexdigest()

def hash_phone(phone: str) -> str:
    if not phone:
        return ""
    return hashlib.sha256(phone.strip().encode()).hexdigest()