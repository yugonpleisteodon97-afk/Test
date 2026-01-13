"""
User and authentication models for Radar application.

Implements User, Role, and MFA token models with secure password hashing
and OAuth support.
"""

from app.extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import uuid
import enum
from typing import Optional


class UserRole(enum.Enum):
    """User role enumeration."""
    CEO = 'CEO'
    CFO = 'CFO'
    ADMIN = 'Admin'


class User(db.Model, UserMixin):
    """
    User model with authentication and authorization.
    
    Supports:
    - Password-based authentication (bcrypt)
    - OAuth (Google, Microsoft)
    - Multi-factor authentication (TOTP)
    - Role-based access control
    """
    
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)  # Nullable for OAuth-only users
    
    # Profile
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.CEO)
    
    # MFA
    mfa_secret = db.Column(db.Text, nullable=True)  # Encrypted TOTP secret
    mfa_enabled = db.Column(db.Boolean, default=False, nullable=False)
    backup_codes = db.Column(db.Text, nullable=True)  # JSON array of hashed backup codes
    
    # OAuth
    oauth_provider = db.Column(db.String(50), nullable=True)  # 'google', 'microsoft', None
    oauth_id = db.Column(db.String(255), nullable=True)  # OAuth provider user ID
    oauth_token = db.Column(db.Text, nullable=True)  # Encrypted OAuth access token
    
    # Account status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)  # Email verification
    verification_token = db.Column(db.String(100), nullable=True)
    verification_expires = db.Column(db.DateTime, nullable=True)
    
    # Security
    failed_login_attempts = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime, nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    password_changed_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    companies = db.relationship('Company', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    reports = db.relationship('Report', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        """Initialize User with password hashing if provided."""
        if 'password' in kwargs:
            password = kwargs.pop('password')
            kwargs['password_hash'] = generate_password_hash(password)
        super(User, self).__init__(**kwargs)
    
    def set_password(self, password: str):
        """
        Set password with bcrypt hashing.
        
        Args:
            password: Plaintext password
        """
        self.password_hash = generate_password_hash(password)
        self.password_changed_at = datetime.utcnow()
    
    def check_password(self, password: str) -> bool:
        """
        Verify password against hash.
        
        Args:
            password: Plaintext password to verify
            
        Returns:
            True if password matches, False otherwise
        """
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def is_locked(self) -> bool:
        """
        Check if account is locked due to failed login attempts.
        
        Returns:
            True if account is locked, False otherwise
        """
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until
    
    def lock_account(self, duration_minutes: int = 15):
        """
        Lock account after failed login attempts.
        
        Args:
            duration_minutes: Lock duration in minutes
        """
        self.locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        self.failed_login_attempts = 0  # Reset counter after locking
        db.session.commit()
    
    def record_failed_login(self, max_attempts: int = 5):
        """
        Record failed login attempt and lock if threshold reached.
        
        Args:
            max_attempts: Maximum failed attempts before locking
        """
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= max_attempts:
            self.lock_account()
        db.session.commit()
    
    def record_successful_login(self):
        """Record successful login and reset failed attempts."""
        self.failed_login_attempts = 0
        self.last_login = datetime.utcnow()
        self.locked_until = None
        db.session.commit()
    
    def has_role(self, role: UserRole) -> bool:
        """
        Check if user has specific role.
        
        Args:
            role: Role to check
            
        Returns:
            True if user has role, False otherwise
        """
        return self.role == role
    
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == UserRole.ADMIN
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Convert user to dictionary representation.
        
        Args:
            include_sensitive: If True, includes sensitive fields
            
        Returns:
            User dictionary
        """
        data = {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'role': self.role.value if self.role else None,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'mfa_enabled': self.mfa_enabled,
            'oauth_provider': self.oauth_provider,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
        
        if include_sensitive:
            data['failed_login_attempts'] = self.failed_login_attempts
            data['locked_until'] = self.locked_until.isoformat() if self.locked_until else None
        
        return data
    
    def __repr__(self):
        return f'<User {self.email}>'


class PasswordResetToken(db.Model):
    """
    Password reset token model.
    
    Stores time-limited tokens for password reset functionality.
    """
    
    __tablename__ = 'password_reset_tokens'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    token = db.Column(db.String(100), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    used = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='password_reset_tokens')
    
    def is_valid(self) -> bool:
        """
        Check if token is valid (not expired and not used).
        
        Returns:
            True if token is valid, False otherwise
        """
        if self.used:
            return False
        if datetime.utcnow() > self.expires_at:
            return False
        return True
    
    def mark_as_used(self):
        """Mark token as used."""
        self.used = True
        db.session.commit()
    
    def __repr__(self):
        return f'<PasswordResetToken {self.token[:8]}...>'
