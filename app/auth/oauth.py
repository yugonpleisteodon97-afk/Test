"""
OAuth integration for Radar application.

Implements Google and Microsoft Azure AD OAuth 2.0 flows.
"""

from flask import Blueprint, request, jsonify, redirect, url_for, session, current_app
from app.extensions import db
from app.auth.models import User, UserRole
from app.auth.services import AuthService
from app.utils.security import get_security_manager
import requests
from typing import Tuple, Optional, Dict, Any
import logging


logger = logging.getLogger(__name__)

# OAuth endpoints
GOOGLE_AUTHORIZATION_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v2/userinfo'

MICROSOFT_AUTHORIZATION_URL = 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize'
MICROSOFT_TOKEN_URL = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'
MICROSOFT_USERINFO_URL = 'https://graph.microsoft.com/v1.0/me'


class OAuthService:
    """Service for OAuth operations."""
    
    @staticmethod
    def get_google_authorization_url(redirect_uri: str) -> str:
        """
        Generate Google OAuth authorization URL.
        
        Args:
            redirect_uri: OAuth callback URL
            
        Returns:
            Authorization URL string
        """
        params = {
            'client_id': current_app.config.get('GOOGLE_CLIENT_ID'),
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': 'openid email profile',
            'access_type': 'offline',
            'prompt': 'consent'
        }
        
        query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
        return f"{GOOGLE_AUTHORIZATION_URL}?{query_string}"
    
    @staticmethod
    def get_microsoft_authorization_url(redirect_uri: str) -> str:
        """
        Generate Microsoft OAuth authorization URL.
        
        Args:
            redirect_uri: OAuth callback URL
            
        Returns:
            Authorization URL string
        """
        params = {
            'client_id': current_app.config.get('MICROSOFT_CLIENT_ID'),
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': 'openid email profile',
            'response_mode': 'query'
        }
        
        query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
        return f"{MICROSOFT_AUTHORIZATION_URL}?{query_string}"
    
    @staticmethod
    def exchange_google_code(code: str, redirect_uri: str) -> Tuple[Optional[Dict[str, Any]], bool, str]:
        """
        Exchange Google authorization code for access token and user info.
        
        Args:
            code: Authorization code from callback
            redirect_uri: OAuth callback URL
            
        Returns:
            Tuple of (user_info, success, message)
        """
        try:
            # Exchange code for token
            token_data = {
                'code': code,
                'client_id': current_app.config.get('GOOGLE_CLIENT_ID'),
                'client_secret': current_app.config.get('GOOGLE_CLIENT_SECRET'),
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code'
            }
            
            response = requests.post(GOOGLE_TOKEN_URL, data=token_data)
            if response.status_code != 200:
                return None, False, f"Token exchange failed: {response.text}"
            
            token_info = response.json()
            access_token = token_info.get('access_token')
            
            if not access_token:
                return None, False, "No access token received"
            
            # Get user info
            headers = {'Authorization': f'Bearer {access_token}'}
            user_response = requests.get(GOOGLE_USERINFO_URL, headers=headers)
            if user_response.status_code != 200:
                return None, False, f"User info fetch failed: {user_response.text}"
            
            user_info = user_response.json()
            
            return user_info, True, "OAuth authentication successful"
            
        except Exception as e:
            logger.error(f"Error exchanging Google OAuth code: {str(e)}", exc_info=True)
            return None, False, f"OAuth error: {str(e)}"
    
    @staticmethod
    def exchange_microsoft_code(code: str, redirect_uri: str) -> Tuple[Optional[Dict[str, Any]], bool, str]:
        """
        Exchange Microsoft authorization code for access token and user info.
        
        Args:
            code: Authorization code from callback
            redirect_uri: OAuth callback URL
            
        Returns:
            Tuple of (user_info, success, message)
        """
        try:
            # Exchange code for token
            token_data = {
                'code': code,
                'client_id': current_app.config.get('MICROSOFT_CLIENT_ID'),
                'client_secret': current_app.config.get('MICROSOFT_CLIENT_SECRET'),
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code',
                'scope': 'openid email profile'
            }
            
            response = requests.post(MICROSOFT_TOKEN_URL, data=token_data)
            if response.status_code != 200:
                return None, False, f"Token exchange failed: {response.text}"
            
            token_info = response.json()
            access_token = token_info.get('access_token')
            
            if not access_token:
                return None, False, "No access token received"
            
            # Get user info
            headers = {'Authorization': f'Bearer {access_token}'}
            user_response = requests.get(MICROSOFT_USERINFO_URL, headers=headers)
            if user_response.status_code != 200:
                return None, False, f"User info fetch failed: {user_response.text}"
            
            user_info = user_response.json()
            
            return user_info, True, "OAuth authentication successful"
            
        except Exception as e:
            logger.error(f"Error exchanging Microsoft OAuth code: {str(e)}", exc_info=True)
            return None, False, f"OAuth error: {str(e)}"
    
    @staticmethod
    def create_or_update_user_from_oauth(
        provider: str,
        oauth_id: str,
        email: str,
        first_name: str,
        last_name: str,
        access_token: str = None
    ) -> Tuple[Optional[User], bool, str]:
        """
        Create or update user from OAuth provider.
        
        Args:
            provider: OAuth provider name ('google' or 'microsoft')
            oauth_id: OAuth provider user ID
            email: User email address
            first_name: User first name
            last_name: User last name
            access_token: OAuth access token (optional, for storage)
            
        Returns:
            Tuple of (user, success, message)
        """
        try:
            email = email.strip().lower()
            
            # Check if user exists by email
            user = User.query.filter_by(email=email).first()
            
            if user:
                # Update existing user with OAuth info
                if not user.oauth_provider:
                    # Link OAuth to existing account
                    user.oauth_provider = provider
                    user.oauth_id = oauth_id
                    if access_token:
                        security_manager = get_security_manager()
                        user.oauth_token = security_manager.encrypt(access_token)
                    user.is_verified = True  # OAuth emails are pre-verified
                    db.session.commit()
                    logger.info(f"OAuth linked to existing account: {email}")
                return user, True, "OAuth authentication successful"
            
            # Create new user
            user = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                role=UserRole.CEO,  # Default role
                oauth_provider=provider,
                oauth_id=oauth_id,
                is_verified=True,  # OAuth emails are pre-verified
                password_hash=None  # No password for OAuth-only users
            )
            
            if access_token:
                security_manager = get_security_manager()
                user.oauth_token = security_manager.encrypt(access_token)
            
            db.session.add(user)
            db.session.commit()
            
            logger.info(f"OAuth user created: {email}")
            return user, True, "OAuth user created successfully"
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating OAuth user: {str(e)}", exc_info=True)
            return None, False, f"Error creating user: {str(e)}"
