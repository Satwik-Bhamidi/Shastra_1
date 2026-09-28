"""
SHASTRA Password Security Module

Secure password hashing using Argon2id algorithm.
Industry-standard password security for offline authentication.
"""

import secrets
import hashlib
import base64
from typing import Tuple


# Argon2 parameters (tuned for security vs performance balance)
# These are conservative defaults suitable for desktop applications
ARGON2_TIME_COST = 3        # Number of iterations
ARGON2_MEMORY_COST = 65536  # Memory in KiB (64 MB)
ARGON2_PARALLELISM = 4      # Number of parallel threads
ARGON2_HASH_LENGTH = 32     # Output hash length in bytes
ARGON2_SALT_LENGTH = 16     # Salt length in bytes


def _try_argon2() -> bool:
    """Check if argon2-cffi is available."""
    try:
        import argon2
        return True
    except ImportError:
        return False


def _hash_with_argon2(password: str) -> str:
    """
    Hash password using Argon2id (preferred method).
    
    Args:
        password: Plain text password
        
    Returns:
        str: Argon2 encoded hash string
    """
    from argon2 import PasswordHasher
    from argon2.profiles import RFC_9106_LOW_MEMORY
    
    # Use RFC 9106 low memory profile - suitable for desktop apps
    ph = PasswordHasher.from_parameters(RFC_9106_LOW_MEMORY)
    return ph.hash(password)


def _verify_with_argon2(password: str, hash_string: str) -> bool:
    """
    Verify password against Argon2 hash.
    
    Args:
        password: Plain text password to verify
        hash_string: Stored Argon2 hash
        
    Returns:
        bool: True if password matches
    """
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError, InvalidHashError
    from argon2.profiles import RFC_9106_LOW_MEMORY
    
    ph = PasswordHasher.from_parameters(RFC_9106_LOW_MEMORY)
    try:
        ph.verify(hash_string, password)
        return True
    except (VerifyMismatchError, InvalidHashError):
        return False


def _hash_with_pbkdf2(password: str) -> str:
    """
    Fallback hash using PBKDF2-SHA256 (if argon2 unavailable).
    
    Args:
        password: Plain text password
        
    Returns:
        str: Encoded hash string with salt
    """
    salt = secrets.token_bytes(ARGON2_SALT_LENGTH)
    hash_bytes = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        iterations=600000,  # OWASP recommended minimum
        dklen=ARGON2_HASH_LENGTH
    )
    # Format: pbkdf2$salt$hash (base64 encoded)
    salt_b64 = base64.b64encode(salt).decode('ascii')
    hash_b64 = base64.b64encode(hash_bytes).decode('ascii')
    return f"pbkdf2${salt_b64}${hash_b64}"


def _verify_with_pbkdf2(password: str, hash_string: str) -> bool:
    """
    Verify password against PBKDF2 hash.
    
    Args:
        password: Plain text password to verify
        hash_string: Stored PBKDF2 hash
        
    Returns:
        bool: True if password matches
    """
    try:
        parts = hash_string.split('$')
        if len(parts) != 3 or parts[0] != 'pbkdf2':
            return False
        
        salt = base64.b64decode(parts[1])
        stored_hash = base64.b64decode(parts[2])
        
        computed_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            iterations=600000,
            dklen=ARGON2_HASH_LENGTH
        )
        
        return secrets.compare_digest(computed_hash, stored_hash)
    except Exception:
        return False


def hash_password(password: str) -> str:
    """
    Hash a password using the best available algorithm.
    Prefers Argon2id, falls back to PBKDF2-SHA256.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        str: Hashed password string (safe for storage)
        
    Security notes:
        - Uses Argon2id when available (memory-hard, GPU-resistant)
        - Falls back to PBKDF2-SHA256 with 600k iterations
        - Both methods use cryptographically secure random salts
        - Output includes algorithm identifier for future-proofing
    """
    if _try_argon2():
        return _hash_with_argon2(password)
    else:
        return _hash_with_pbkdf2(password)


def verify_password(password: str, hash_string: str) -> bool:
    """
    Verify a password against a stored hash.
    Automatically detects hash algorithm from the stored string.
    
    Args:
        password: Plain text password to verify
        hash_string: Stored hash string
        
    Returns:
        bool: True if password is correct, False otherwise
        
    Security notes:
        - Uses constant-time comparison to prevent timing attacks
        - Handles both Argon2 and PBKDF2 hash formats
    """
    if not password or not hash_string:
        return False
    
    # Detect hash type
    if hash_string.startswith('$argon2'):
        if _try_argon2():
            return _verify_with_argon2(password, hash_string)
        else:
            # Argon2 hash but library not available
            return False
    elif hash_string.startswith('pbkdf2$'):
        return _verify_with_pbkdf2(password, hash_string)
    else:
        # Unknown hash format
        return False


def generate_temporary_password(length: int = 12) -> str:
    """
    Generate a cryptographically secure temporary password.
    
    Args:
        length: Password length (default 12)
        
    Returns:
        str: Random password string
    """
    # Use alphanumeric characters for easy typing
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password meets minimum security requirements.
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    
    return True, ""
