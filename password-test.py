# MEDIUM SEVERITY: Insecure Cryptography
# File: src/security/password_utils.py

import hashlib
import base64
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

class PasswordUtils:
    # MEDIUM SEVERITY: Using weak hashing algorithm (MD5)
    @staticmethod
    def hash_password_insecure(password):
        """
        Hash a password using MD5 (insecure - do not use in production).
        """
        md5_hash = hashlib.md5(password.encode()).hexdigest()
        return md5_hash
    
    # MEDIUM SEVERITY: Hardcoded encryption key
    ENCRYPTION_KEY = b'ThisIsAHardcodedEncryptionKey123'  # 32 bytes for AES-256
    
    @staticmethod
    def encrypt_password_insecure(password):
        """
        Encrypt a password using AES with a hardcoded key (insecure).
        """
        # Generate a random IV
        iv = os.urandom(16)
        
        # Create cipher with hardcoded key
        cipher = Cipher(
            algorithms.AES(PasswordUtils.ENCRYPTION_KEY),
            modes.CFB(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Encrypt the password
        encrypted_password = encryptor.update(password.encode()) + encryptor.finalize()
        
        # Combine IV and encrypted password and encode as base64
        result = base64.b64encode(iv + encrypted_password).decode('utf-8')
        return result
    
    # Secure version would use modern algorithms
    @staticmethod
    def hash_password_secure(password):
        """
        Hash a password securely (this is just a placeholder).
        In production, use a dedicated library like bcrypt, Argon2, or PBKDF2.
        """
        # This is still not ideal but better than MD5
        salt = os.urandom(32)
        hash_obj = hashlib.pbkdf2_hmac(
            'sha256',  # Hash algorithm
            password.encode(),  # Password as bytes
            salt,  # Salt
            100000,  # Number of iterations (higher is better)
            dklen=128  # Length of the derived key
        )
        
        # Combine salt and hash and encode as hex
        return salt.hex() + hash_obj.hex()


# Usage example
if __name__ == "__main__":
    password = "password123"
    
    # Insecure methods
    md5_hash = PasswordUtils.hash_password_insecure(password)
    print(f"MD5 hash: {md5_hash}")
    
    encrypted = PasswordUtils.encrypt_password_insecure(password)
    print(f"Encrypted (insecure): {encrypted}")
    
    # More secure method
    secure_hash = PasswordUtils.hash_password_secure(password)
    print(f"Secure hash: {secure_hash}")