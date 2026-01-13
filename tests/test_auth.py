"""Tests for authentication module."""

import pytest
from app.auth.models import User, UserRole
from app.auth.services import AuthService
from app.extensions import db


class TestAuthService:
    """Test authentication service."""
    
    def test_register_user(self, app):
        """Test user registration."""
        with app.app_context():
            user, success, message = AuthService.register_user(
                email='newuser@example.com',
                password='SecurePassword123!',
                first_name='New',
                last_name='User',
                role='CEO'
            )
            
            assert success is True
            assert user is not None
            assert user.email == 'newuser@example.com'
            assert user.role == UserRole.CEO
    
    def test_authenticate_user(self, app, test_user):
        """Test user authentication."""
        with app.app_context():
            user, success, message = AuthService.authenticate_user(
                email='test@example.com',
                password='TestPassword123!'
            )
            
            assert success is True
            assert user is not None
            assert user.email == 'test@example.com'
    
    def test_authenticate_user_invalid_password(self, app, test_user):
        """Test authentication with invalid password."""
        with app.app_context():
            user, success, message = AuthService.authenticate_user(
                email='test@example.com',
                password='WrongPassword123!'
            )
            
            assert success is False
            assert user is None
    
    def test_generate_jwt_tokens(self, app, test_user):
        """Test JWT token generation."""
        with app.app_context():
            tokens = AuthService.generate_jwt_tokens(test_user)
            
            assert 'access_token' in tokens
            assert 'refresh_token' in tokens
            assert tokens['access_token'] is not None
            assert tokens['refresh_token'] is not None


class TestUserModel:
    """Test User model."""
    
    def test_user_password_hashing(self, app):
        """Test password hashing."""
        with app.app_context():
            user = User(
                email='hash@example.com',
                first_name='Hash',
                last_name='Test',
                role=UserRole.CEO
            )
            user.set_password('TestPassword123!')
            
            assert user.password_hash is not None
            assert user.check_password('TestPassword123!') is True
            assert user.check_password('WrongPassword') is False
    
    def test_user_role_check(self, app):
        """Test user role checking."""
        with app.app_context():
            user = User(
                email='role@example.com',
                first_name='Role',
                last_name='Test',
                role=UserRole.CEO
            )
            
            assert user.has_role(UserRole.CEO) is True
            assert user.has_role(UserRole.CFO) is False
            assert user.is_admin() is False
