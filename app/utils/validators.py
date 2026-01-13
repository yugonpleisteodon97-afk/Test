"""
Input validation utilities for Radar application.

Provides validation functions for user inputs, API payloads,
and data integrity checks.
"""

import re
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse
from datetime import datetime, date, timedelta


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


def validate_url(url: str, require_https: bool = True) -> str:
    """
    Validate and normalize URL.
    
    Args:
        url: URL string to validate
        require_https: If True, requires HTTPS (except localhost)
        
    Returns:
        Normalized URL string
    
    Raises:
        ValidationError: If URL is invalid
    """
    if not url or not isinstance(url, str):
        raise ValidationError("URL is required and must be a string")
    
    url = url.strip()
    
    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = f"https://{url}"
    
    try:
        parsed = urlparse(url)
    except Exception as e:
        raise ValidationError(f"Invalid URL format: {str(e)}")
    
    if not parsed.netloc:
        raise ValidationError("URL must have a valid domain")
    
    # Require HTTPS in production
    if require_https and parsed.scheme != 'https' and 'localhost' not in parsed.netloc:
        raise ValidationError("URL must use HTTPS")
    
    return url


def validate_email(email: str) -> str:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        Normalized email string
    
    Raises:
        ValidationError: If email is invalid
    """
    if not email or not isinstance(email, str):
        raise ValidationError("Email is required and must be a string")
    
    email = email.strip().lower()
    
    # RFC 5322 compliant regex (simplified)
    pattern = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    if not pattern.match(email):
        raise ValidationError(f"Invalid email format: {email}")
    
    # Additional checks
    if len(email) > 254:  # RFC 5321 limit
        raise ValidationError("Email address too long")
    
    if email.count('@') != 1:
        raise ValidationError("Email must contain exactly one @ symbol")
    
    local, domain = email.split('@')
    if len(local) > 64:  # RFC 5321 limit
        raise ValidationError("Email local part too long")
    
    return email


def validate_password(password: str, min_length: int = 12) -> str:
    """
    Validate password strength.
    
    Requires:
    - Minimum length (default 12)
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    
    Args:
        password: Password to validate
        min_length: Minimum password length
        
    Returns:
        Password string if valid
    
    Raises:
        ValidationError: If password doesn't meet requirements
    """
    if not password or not isinstance(password, str):
        raise ValidationError("Password is required and must be a string")
    
    if len(password) < min_length:
        raise ValidationError(f"Password must be at least {min_length} characters long")
    
    if not re.search(r'[A-Z]', password):
        raise ValidationError("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        raise ValidationError("Password must contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        raise ValidationError("Password must contain at least one digit")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValidationError("Password must contain at least one special character")
    
    # Check for common passwords (basic check)
    common_passwords = ['password', '123456', 'qwerty', 'abc123']
    if password.lower() in common_passwords:
        raise ValidationError("Password is too common. Please choose a stronger password")
    
    return password


def validate_role(role: str) -> str:
    """
    Validate user role.
    
    Args:
        role: Role string to validate
        
    Returns:
        Validated role string
    
    Raises:
        ValidationError: If role is invalid
    """
    valid_roles = ['CEO', 'CFO', 'Admin']
    
    if not role or not isinstance(role, str):
        raise ValidationError("Role is required and must be a string")
    
    role = role.strip()
    
    if role not in valid_roles:
        raise ValidationError(f"Invalid role: {role}. Must be one of {valid_roles}")
    
    return role


def validate_confidence_score(score: float) -> float:
    """
    Validate confidence score (0-100).
    
    Args:
        score: Confidence score to validate
        
    Returns:
        Validated score
    
    Raises:
        ValidationError: If score is out of range
    """
    try:
        score = float(score)
    except (ValueError, TypeError):
        raise ValidationError("Confidence score must be a number")
    
    if not (0 <= score <= 100):
        raise ValidationError(f"Confidence score must be between 0 and 100, got {score}")
    
    return score


def validate_threat_score(score: float) -> float:
    """
    Validate threat score (1-10).
    
    Args:
        score: Threat score to validate
        
    Returns:
        Validated score
    
    Raises:
        ValidationError: If score is out of range
    """
    try:
        score = float(score)
    except (ValueError, TypeError):
        raise ValidationError("Threat score must be a number")
    
    if not (1 <= score <= 10):
        raise ValidationError(f"Threat score must be between 1 and 10, got {score}")
    
    return score


def validate_date_range(start_date: date, end_date: date) -> tuple:
    """
    Validate date range.
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        Tuple of (start_date, end_date) if valid
    
    Raises:
        ValidationError: If date range is invalid
    """
    if not isinstance(start_date, date) or not isinstance(end_date, date):
        raise ValidationError("Start and end dates must be date objects")
    
    if start_date > end_date:
        raise ValidationError("Start date must be before or equal to end date")
    
    # Check reasonable range (e.g., not more than 5 years)
    max_range = timedelta(days=365 * 5)
    if end_date - start_date > max_range:
        raise ValidationError("Date range cannot exceed 5 years")
    
    return start_date, end_date


def validate_json_structure(data: Dict[str, Any], required_keys: List[str]) -> Dict[str, Any]:
    """
    Validate JSON structure has required keys.
    
    Args:
        data: JSON data to validate
        required_keys: List of required key paths (e.g., ['user.email', 'user.name'])
        
    Returns:
        Validated data dictionary
    
    Raises:
        ValidationError: If required keys are missing
    """
    if not isinstance(data, dict):
        raise ValidationError("Data must be a dictionary")
    
    missing_keys = []
    for key_path in required_keys:
        keys = key_path.split('.')
        current = data
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                missing_keys.append(key_path)
                break
            current = current[key]
    
    if missing_keys:
        raise ValidationError(f"Missing required keys: {', '.join(missing_keys)}")
    
    return data
