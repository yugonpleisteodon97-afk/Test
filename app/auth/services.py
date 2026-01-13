"""
Authentication services for Radar application.

Implements business logic for authentication, authorization, and user management.
"""

from app.extensions import db
from app.auth.models import User, UserRole, PasswordResetToken
from app.utils.security import get_security_manager, validate_email, sanitize_input
from app.utils.validators import validate_password, validate_role
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, get_jwt
from flask_login import login_user
from datetime import datetime, timedelta
import secrets
import hashlib
from typing import Optional, Tuple, Dict, Any
import logging


logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication and user management operations."""
    
    @staticmethod
    def register_user(
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        role: str = 'CEO'
    ) -> Tuple[User, bool, str]:
        """
        Register a new user.
        
        Args:
            email: User email address
            password: Plaintext password
            first_name: User first name
            last_name: User last name
            role: User role (CEO, CFO, Admin)
            
        Returns:
            Tuple of (user, success, message)
        """
        try:
            # Validate inputs
            email = validate_email(email.strip().lower())
            validate_password(password)
            validate_role(role)
            first_name = sanitize_input(first_name.strip())
            last_name = sanitize_input(last_name.strip())
            
            # Check if user already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                return None, False, "User with this email already exists"
            
            # Create user
            user = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                role=UserRole[role.upper()]
            )
            user.set_password(password)
            user.is_verified = False  # Require email verification
            
            db.session.add(user)
            db.session.commit()
            
            logger.info(f"User registered: {email}")
            return user, True, "User registered successfully"
            
        except ValueError as e:
            return None, False, str(e)
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error registering user: {str(e)}", exc_info=True)
            return None, False, "An error occurred during registration"
    
    @staticmethod
    def authenticate_user(email: str, password: str) -> Tuple[Optional[User], bool, str]:
        """
        Authenticate user with email and password.
        
        Args:
            email: User email address
            password: Plaintext password
            
        Returns:
            Tuple of (user, success, message)
        """
        try:
            email = email.strip().lower()
            
            # Find user
            user = User.query.filter_by(email=email).first()
            if not user:
                return None, False, "Invalid email or password"
            
            # Check if account is locked
            if user.is_locked():
                remaining_time = (user.locked_until - datetime.utcnow()).total_seconds() / 60
                return None, False, f"Account is locked. Please try again in {int(remaining_time)} minutes."
            
            # Check if account is active
            if not user.is_active:
                return None, False, "Account is deactivated. Please contact support."
            
            # Verify password
            if not user.check_password(password):
                user.record_failed_login(max_attempts=5)
                return None, False, "Invalid email or password"
            
            # Successful login
            user.record_successful_login()
            login_user(user, remember=False)
            
            logger.info(f"User authenticated: {email}")
            return user, True, "Authentication successful"
            
        except Exception as e:
            logger.error(f"Error authenticating user: {str(e)}", exc_info=True)
            return None, False, "An error occurred during authentication"
    
    @staticmethod
    def generate_jwt_tokens(user: User) -> Dict[str, str]:
        """
        Generate JWT access and refresh tokens for user.
        
        Args:
            user: User object
            
        Returns:
            Dictionary with access_token and refresh_token
        """
        # Create token claims
        additional_claims = {
            'role': user.role.value if user.role else None,
            'email': user.email,
            'mfa_enabled': user.mfa_enabled
        }
        
        # Create tokens
        access_token = create_access_token(
            identity=user.id,
            additional_claims=additional_claims
        )
        refresh_token = create_refresh_token(
            identity=user.id,
            additional_claims=additional_claims
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token
        }
    
    @staticmethod
    def create_password_reset_token(email: str) -> Tuple[Optional[PasswordResetToken], bool, str]:
        """
        Create password reset token for user.
        
        Args:
            email: User email address
            
        Returns:
            Tuple of (token, success, message)
        """
        try:
            email = email.strip().lower()
            user = User.query.filter_by(email=email).first()
            
            if not user:
                # Don't reveal if user exists for security
                return None, True, "If an account exists with this email, a password reset link has been sent"
            
            # Generate secure token
            token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiration
            
            # Invalidate existing tokens for this user
            PasswordResetToken.query.filter_by(user_id=user.id, used=False).update({'used': True})
            
            # Create new token
            reset_token = PasswordResetToken(
                user_id=user.id,
                token=token,
                expires_at=expires_at
            )
            
            db.session.add(reset_token)
            db.session.commit()
            
            logger.info(f"Password reset token created for: {email}")
            return reset_token, True, "Password reset token created"
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating password reset token: {str(e)}", exc_info=True)
            return None, False, "An error occurred while creating password reset token"
    
    @staticmethod
    def reset_password(token: str, new_password: str) -> Tuple[bool, str]:
        """
        Reset user password using reset token.
        
        Args:
            token: Password reset token
            new_password: New plaintext password
            
        Returns:
            Tuple of (success, message)
        """
        try:
            validate_password(new_password)
            
            # Find token
            reset_token = PasswordResetToken.query.filter_by(token=token, used=False).first()
            if not reset_token:
                return False, "Invalid or expired reset token"
            
            # Check if token is valid
            if not reset_token.is_valid():
                reset_token.mark_as_used()
                return False, "Invalid or expired reset token"
            
            # Reset password
            user = reset_token.user
            user.set_password(new_password)
            reset_token.mark_as_used()
            
            db.session.commit()
            
            logger.info(f"Password reset for user: {user.email}")
            return True, "Password reset successful"
            
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error resetting password: {str(e)}", exc_info=True)
            return False, "An error occurred while resetting password"
    
    @staticmethod
    def change_password(user: User, current_password: str, new_password: str) -> Tuple[bool, str]:
        """
        Change user password (requires current password).
        
        Args:
            user: User object
            current_password: Current plaintext password
            new_password: New plaintext password
            
        Returns:
            Tuple of (success, message)
        """
        try:
            validate_password(new_password)
            
            # Verify current password
            if not user.check_password(current_password):
                return False, "Current password is incorrect"
            
            # Set new password
            user.set_password(new_password)
            db.session.commit()
            
            logger.info(f"Password changed for user: {user.email}")
            return True, "Password changed successfully"
            
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error changing password: {str(e)}", exc_info=True)
            return False, "An error occurred while changing password"
    
    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User object or None
        """
        return User.query.filter_by(id=user_id).first()
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """
        Get user by email.
        
        Args:
            email: User email address
            
        Returns:
            User object or None
        """
        return User.query.filter_by(email=email.strip().lower()).first()
