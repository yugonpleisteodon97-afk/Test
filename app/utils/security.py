"""
Security utilities for Radar application.

Implements encryption, decryption, and sanitization functions using
industry-standard libraries (Fernet for encryption, bleach for sanitization).
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import bleach
import re
from typing import Optional


class SecurityManager:
    """
    Manages encryption and security operations for sensitive data.
    
    Uses Fernet (symmetric encryption) for encrypting API keys, MFA secrets,
    and other sensitive configuration data. Supports key derivation from
    passwords for enhanced security.
    """
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize SecurityManager with encryption key.
        
        Args:
            encryption_key: Base64-encoded Fernet key. If None, generates new key.
        """
        if encryption_key:
            # Use provided key (should be from environment variable)
            if isinstance(encryption_key, str):
                # Ensure it's properly formatted
                try:
                    self._key = encryption_key.encode() if not encryption_key.endswith('=') else encryption_key.encode()
                    # Validate key
                    Fernet(self._key)
                except Exception:
                    # Generate from seed if invalid
                    self._key = self._derive_key(encryption_key)
            else:
                self._key = encryption_key
        else:
            # Generate new key (for development/testing only)
            self._key = Fernet.generate_key()
        
        self._cipher = Fernet(self._key)
    
    @staticmethod
    def _derive_key(password: str, salt: Optional[bytes] = None) -> bytes:
        """
        Derive a Fernet key from a password using PBKDF2.
        
        Args:
            password: Password to derive key from
            salt: Salt for key derivation (generates if None)
            
        Returns:
            Base64-encoded Fernet key
        """
        if salt is None:
            salt = b'radar_salt_v1'  # Fixed salt for consistency (use random in production)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt sensitive data (API keys, MFA secrets, etc.).
        
        Args:
            data: Plaintext string to encrypt
            
        Returns:
            Encrypted string (base64-encoded)
        
        Raises:
            ValueError: If data is not a string
        """
        if not isinstance(data, str):
            raise ValueError("Data must be a string")
        
        encrypted = self._cipher.encrypt(data.encode())
        return encrypted.decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive data.
        
        Args:
            encrypted_data: Encrypted string (base64-encoded)
            
        Returns:
            Decrypted plaintext string
        
        Raises:
            ValueError: If decryption fails (invalid key or corrupted data)
        """
        try:
            decrypted = self._cipher.decrypt(encrypted_data.encode())
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")
    
    def get_key(self) -> str:
        """
        Get the encryption key (for backup/configuration purposes).
        
        Returns:
            Base64-encoded encryption key
        """
        return self._key.decode()


# Global security manager instance (initialized in app factory)
_security_manager: Optional[SecurityManager] = None


def init_security_manager(encryption_key: str):
    """
    Initialize global security manager.
    
    Args:
        encryption_key: Encryption key from configuration
    """
    global _security_manager
    _security_manager = SecurityManager(encryption_key)


def get_security_manager() -> SecurityManager:
    """
    Get global security manager instance.
    
    Returns:
        SecurityManager instance
    
    Raises:
        RuntimeError: If security manager not initialized
    """
    if _security_manager is None:
        raise RuntimeError("Security manager not initialized. Call init_security_manager() first.")
    return _security_manager


# Allowed HTML tags and attributes for sanitization
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'blockquote', 'code', 'pre'
]

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    'code': ['class']
}


def sanitize_input(data: str, allow_html: bool = False) -> str:
    """
    Sanitize user input to prevent XSS attacks.
    
    Args:
        data: Input string to sanitize
        allow_html: If True, allows safe HTML tags. If False, strips all HTML.
        
    Returns:
        Sanitized string
    """
    if not isinstance(data, str):
        return str(data)
    
    if allow_html:
        # Allow safe HTML tags
        sanitized = bleach.clean(
            data,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            strip=True
        )
    else:
        # Strip all HTML
        sanitized = bleach.clean(data, tags=[], strip=True)
    
    return sanitized


def sanitize_url(url: str) -> str:
    """
    Sanitize and validate URL.
    
    Args:
        url: URL string to sanitize
        
    Returns:
        Sanitized URL
    
    Raises:
        ValueError: If URL is invalid
    """
    if not url:
        raise ValueError("URL cannot be empty")
    
    url = url.strip()
    
    # Basic URL validation
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    
    if not url_pattern.match(url):
        raise ValueError(f"Invalid URL format: {url}")
    
    return url


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not email:
        return False
    
    email_pattern = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    return bool(email_pattern.match(email.strip()))
