import os
from cryptography.fernet import Fernet
import base64

# This key should be stored in GCP Secret Manager in production.
# For local dev, it falls back to a provided ENCRYPTION_KEY or a default.
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not ENCRYPTION_KEY:
    # In a real SaaS, this would block startup if in production mode
    # For now, we'll generate a consistent one for the workspace if not provided
    # IMPORTANT: In production, this MUST be a 32-byte base64 encoded string
    ENCRYPTION_KEY = base64.urlsafe_b64encode(b"saas_cloud_readiness_default_32b").decode()

cipher_suite = Fernet(ENCRYPTION_KEY.encode())

def encrypt_data(data: str) -> str:
    """Encrypts a string and returns a base64 encoded string."""
    if not data:
        return data
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    """Decrypts a base64 encoded string and returns the original string."""
    if not encrypted_data:
        return encrypted_data
    try:
        return cipher_suite.decrypt(encrypted_data.encode()).decode()
    except Exception as e:
        # If decryption fails (e.g. data was not encrypted), return as is
        # This allows for a graceful migration of old plain-text data
        return encrypted_data
