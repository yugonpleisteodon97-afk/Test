"""
Authentication routes for Radar application.

Handles user registration, login, password management, and OAuth flows.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token, create_refresh_token
from flask_login import login_user, logout_user, login_required
from app.extensions import db, limiter
from app.auth.models import User, UserRole
from app.auth.services import AuthService
from app.auth.decorators import requires_authentication, requires_admin
from app.auth.mfa import MFAService
from app.auth.oauth import OAuthService
from flask_login import login_user
from app.utils.validators import validate_email, ValidationError
from app.utils.rate_limiting import get_client_ip
from datetime import datetime
import logging


logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
@limiter.limit("5 per minute")  # Rate limit registration
def register():
    """
    Register a new user.
    
    Request body:
        {
            "email": "user@example.com",
            "password": "SecurePassword123!",
            "first_name": "John",
            "last_name": "Doe",
            "role": "CEO"  # Optional, defaults to CEO
        }
    
    Returns:
        JSON response with user data and tokens
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Bad Request', 'message': 'Request body required'}), 400
        
        # Validate required fields
        required_fields = ['email', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': 'Bad Request', 'message': f'{field} is required'}), 400
        
        # Register user
        user, success, message = AuthService.register_user(
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=data.get('role', 'CEO')
        )
        
        if not success:
            return jsonify({'error': 'Registration Failed', 'message': message}), 400
        
        # Generate tokens
        tokens = AuthService.generate_jwt_tokens(user)
        
        logger.info(f"User registered: {user.email}")
        
        return jsonify({
            'message': message,
            'user': user.to_dict(include_sensitive=False),
            'tokens': tokens
        }), 201
        
    except ValidationError as e:
        return jsonify({'error': 'Validation Error', 'message': str(e)}), 400
    except Exception as e:
        logger.error(f"Error in registration: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal Server Error', 'message': 'An error occurred during registration'}), 500


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")  # Rate limit login attempts
def login():
    """
    Authenticate user and return JWT tokens.
    
    Request body:
        {
            "email": "user@example.com",
            "password": "SecurePassword123!"
        }
    
    Returns:
        JSON response with user data and tokens
    """
    try:
        data = request.get_json()
        
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Bad Request', 'message': 'Email and password required'}), 400
        
        # Authenticate user
        user, success, message = AuthService.authenticate_user(
            email=data['email'],
            password=data['password']
        )
        
        if not success or not user:
            return jsonify({'error': 'Authentication Failed', 'message': message}), 401
        
        # Check if MFA is enabled
        if user.mfa_enabled:
            # Return partial success - MFA verification required
            return jsonify({
                'message': 'MFA verification required',
                'mfa_required': True,
                'user_id': user.id
            }), 200
        
        # Generate tokens
        tokens = AuthService.generate_jwt_tokens(user)
        
        logger.info(f"User logged in: {user.email}")
        
        return jsonify({
            'message': message,
            'user': user.to_dict(include_sensitive=False),
            'tokens': tokens
        }), 200
        
    except Exception as e:
        logger.error(f"Error in login: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal Server Error', 'message': 'An error occurred during authentication'}), 500


@auth_bp.route('/logout', methods=['POST'])
@requires_authentication
def logout():
    """
    Logout user (invalidates tokens on client side).
    
    Note: JWT tokens are stateless, so actual invalidation requires
    token blacklisting in Redis (implemented in token revocation).
    
    Returns:
        JSON response confirming logout
    """
    try:
        # In a stateless JWT system, logout is primarily client-side
        # Token blacklisting can be implemented using Redis
        logout_user()
        
        logger.info(f"User logged out: {get_jwt_identity()}")
        
        return jsonify({
            'message': 'Logout successful'
        }), 200
        
    except Exception as e:
        logger.error(f"Error in logout: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal Server Error', 'message': 'An error occurred during logout'}), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh access token using refresh token.
    
    Returns:
        JSON response with new access token
    """
    try:
        user_id = get_jwt_identity()
        user = AuthService.get_user_by_id(user_id)
        
        if not user or not user.is_active:
            return jsonify({'error': 'Unauthorized', 'message': 'User not found or inactive'}), 401
        
        # Create new access token
        additional_claims = {
            'role': user.role.value if user.role else None,
            'email': user.email,
            'mfa_enabled': user.mfa_enabled
        }
        
        new_token = create_access_token(
            identity=user.id,
            additional_claims=additional_claims
        )
        
        return jsonify({
            'access_token': new_token
        }), 200
        
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal Server Error', 'message': 'An error occurred during token refresh'}), 500


@auth_bp.route('/password-reset/request', methods=['POST'])
@limiter.limit("5 per hour")  # Rate limit password reset requests
def request_password_reset():
    """
    Request password reset token.
    
    Request body:
        {
            "email": "user@example.com"
        }
    
    Returns:
        JSON response (doesn't reveal if email exists for security)
    """
    try:
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({'error': 'Bad Request', 'message': 'Email required'}), 400
        
        # Create reset token
        reset_token, success, message = AuthService.create_password_reset_token(data['email'])
        
        if success and reset_token:
            # Send email with reset link (implemented in email service)
            # For now, just return success message
            # In production, send email with reset link containing token
            logger.info(f"Password reset token created for: {data['email']}")
            # TODO: Send email via email service
        
        # Always return success message (don't reveal if email exists)
        return jsonify({
            'message': 'If an account exists with this email, a password reset link has been sent'
        }), 200
        
    except Exception as e:
        logger.error(f"Error requesting password reset: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal Server Error', 'message': 'An error occurred'}), 500


@auth_bp.route('/password-reset/confirm', methods=['POST'])
@limiter.limit("10 per hour")  # Rate limit password reset confirmations
def confirm_password_reset():
    """
    Reset password using reset token.
    
    Request body:
        {
            "token": "reset-token-here",
            "new_password": "NewSecurePassword123!"
        }
    
    Returns:
        JSON response confirming password reset
    """
    try:
        data = request.get_json()
        
        if not data or 'token' not in data or 'new_password' not in data:
            return jsonify({'error': 'Bad Request', 'message': 'Token and new_password required'}), 400
        
        # Reset password
        success, message = AuthService.reset_password(
            token=data['token'],
            new_password=data['new_password']
        )
        
        if not success:
            return jsonify({'error': 'Password Reset Failed', 'message': message}), 400
        
        logger.info("Password reset successful")
        
        return jsonify({
            'message': message
        }), 200
        
    except Exception as e:
        logger.error(f"Error confirming password reset: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal Server Error', 'message': 'An error occurred'}), 500


@auth_bp.route('/password/change', methods=['POST'])
@requires_authentication
def change_password():
    """
    Change user password (requires current password).
    
    Request body:
        {
            "current_password": "OldPassword123!",
            "new_password": "NewSecurePassword123!"
        }
    
    Returns:
        JSON response confirming password change
    """
    try:
        data = request.get_json()
        
        if not data or 'current_password' not in data or 'new_password' not in data:
            return jsonify({'error': 'Bad Request', 'message': 'current_password and new_password required'}), 400
        
        user_id = get_jwt_identity()
        user = AuthService.get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'Unauthorized', 'message': 'User not found'}), 401
        
        # Change password
        success, message = AuthService.change_password(
            user=user,
            current_password=data['current_password'],
            new_password=data['new_password']
        )
        
        if not success:
            return jsonify({'error': 'Password Change Failed', 'message': message}), 400
        
        logger.info(f"Password changed for user: {user.email}")
        
        return jsonify({
            'message': message
        }), 200
        
    except Exception as e:
        logger.error(f"Error changing password: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal Server Error', 'message': 'An error occurred'}), 500


@auth_bp.route('/me', methods=['GET'])
@requires_authentication
def get_current_user():
    """
    Get current authenticated user information.
    
    Returns:
        JSON response with user data
    """
    try:
        user_id = get_jwt_identity()
        user = AuthService.get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'Unauthorized', 'message': 'User not found'}), 401
        
        return jsonify({
            'user': user.to_dict(include_sensitive=False)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal Server Error', 'message': 'An error occurred'}), 500


@auth_bp.route('/mfa/setup', methods=['POST'])
@requires_authentication
def setup_mfa():
    """
    Start MFA setup process (generate secret and QR code).
    
    Returns:
        JSON response with QR code image and secret (for manual entry)
    """
    try:
        user_id = get_jwt_identity()
        user = AuthService.get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'Unauthorized', 'message': 'User not found'}), 401
        
        if user.mfa_enabled:
            return jsonify({'error': 'Bad Request', 'message': 'MFA is already enabled'}), 400
        
        # Generate secret
        secret = MFAService.generate_mfa_secret()
        
        # Generate QR code
        qr_code = MFAService.generate_qr_code(secret, user.email)
        
        # Store secret temporarily (encrypted) - user needs to verify before enabling
        from app.utils.security import get_security_manager
        security_manager = get_security_manager()
        temp_secret = security_manager.encrypt(secret)
        
        logger.info(f"MFA setup initiated for user: {user.email}")
        
        return jsonify({
            'message': 'MFA setup initiated',
            'qr_code': qr_code,
            'secret': secret,  # Include for manual entry
            'temp_secret': temp_secret  # Store temporarily until verified
        }), 200
        
    except Exception as e:
        logger.error(f"Error setting up MFA: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal Server Error', 'message': 'An error occurred'}), 500


@auth_bp.route('/mfa/enable', methods=['POST'])
@requires_authentication
def enable_mfa():
    """
    Enable MFA after verification code confirmation.
    
    Request body:
        {
            "secret": "TOTP_SECRET_HERE",
            "verification_code": "123456"
        }
    
    Returns:
        JSON response with backup codes
    """
    try:
        data = request.get_json()
        
        if not data or 'secret' not in data or 'verification_code' not in data:
            return jsonify({'error': 'Bad Request', 'message': 'secret and verification_code required'}), 400
        
        user_id = get_jwt_identity()
        user = AuthService.get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'Unauthorized', 'message': 'User not found'}), 401
        
        # Enable MFA
        success, result = MFAService.enable_mfa(
            user=user,
            secret=data['secret'],
            verification_code=data['verification_code']
        )
        
        if not success:
            return jsonify({'error': 'MFA Setup Failed', 'message': str(result)}), 400
        
        logger.info(f"MFA enabled for user: {user.email}")
        
        return jsonify({
            'message': 'MFA enabled successfully',
            'backup_codes': result  # List of backup codes (user should save these)
        }), 200
        
    except Exception as e:
        logger.error(f"Error enabling MFA: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal Server Error', 'message': 'An error occurred'}), 500


@auth_bp.route('/mfa/verify', methods=['POST'])
@limiter.limit("10 per minute")  # Rate limit MFA verification
def verify_mfa():
    """
    Verify MFA code during login.
    
    Request body:
        {
            "user_id": "user-id-here",
            "code": "123456"  # TOTP code or backup code
        }
    
    Returns:
        JSON response with JWT tokens if successful
    """
    try:
        data = request.get_json()
        
        if not data or 'user_id' not in data or 'code' not in data:
            return jsonify({'error': 'Bad Request', 'message': 'user_id and code required'}), 400
        
        user = AuthService.get_user_by_id(data['user_id'])
        if not user:
            return jsonify({'error': 'Unauthorized', 'message': 'User not found'}), 401
        
        # Verify MFA code
        if not MFAService.verify_mfa_code(user, data['code']):
            return jsonify({'error': 'Verification Failed', 'message': 'Invalid MFA code'}), 401
        
        # Generate tokens
        tokens = AuthService.generate_jwt_tokens(user)
        
        logger.info(f"MFA verified for user: {user.email}")
        
        return jsonify({
            'message': 'MFA verification successful',
            'user': user.to_dict(include_sensitive=False),
            'tokens': tokens
        }), 200
        
    except Exception as e:
        logger.error(f"Error verifying MFA: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal Server Error', 'message': 'An error occurred'}), 500


@auth_bp.route('/mfa/disable', methods=['POST'])
@requires_authentication
def disable_mfa():
    """
    Disable MFA for user (requires password verification).
    
    Request body:
        {
            "password": "user-password"
        }
    
    Returns:
        JSON response confirming MFA disable
    """
    try:
        data = request.get_json()
        
        if not data or 'password' not in data:
            return jsonify({'error': 'Bad Request', 'message': 'password required'}), 400
        
        user_id = get_jwt_identity()
        user = AuthService.get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'Unauthorized', 'message': 'User not found'}), 401
        
        # Verify password
        if not user.check_password(data['password']):
            return jsonify({'error': 'Unauthorized', 'message': 'Invalid password'}), 401
        
        # Disable MFA
        success, message = MFAService.disable_mfa(user)
        
        if not success:
            return jsonify({'error': 'MFA Disable Failed', 'message': message}), 400
        
        logger.info(f"MFA disabled for user: {user.email}")
        
        return jsonify({
            'message': message
        }), 200
        
    except Exception as e:
        logger.error(f"Error disabling MFA: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal Server Error', 'message': 'An error occurred'}), 500


@auth_bp.route('/mfa/backup-codes', methods=['POST'])
@requires_authentication
def regenerate_backup_codes():
    """
    Regenerate backup codes for MFA.
    
    Returns:
        JSON response with new backup codes
    """
    try:
        user_id = get_jwt_identity()
        user = AuthService.get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'Unauthorized', 'message': 'User not found'}), 401
        
        if not user.mfa_enabled:
            return jsonify({'error': 'Bad Request', 'message': 'MFA is not enabled'}), 400
        
        # Regenerate backup codes
        success, backup_codes, message = MFAService.regenerate_backup_codes(user)
        
        if not success:
            return jsonify({'error': 'Regeneration Failed', 'message': message}), 400
        
        logger.info(f"Backup codes regenerated for user: {user.email}")
        
        return jsonify({
            'message': message,
            'backup_codes': backup_codes  # User should save these
        }), 200
        
    except Exception as e:
        logger.error(f"Error regenerating backup codes: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal Server Error', 'message': 'An error occurred'}), 500


@auth_bp.route('/oauth/google/authorize', methods=['GET'])
def google_oauth_authorize():
    """
    Initiate Google OAuth flow.
    
    Returns:
        Redirect to Google OAuth authorization page
    """
    try:
        redirect_uri = current_app.config.get('OAUTH_REDIRECT_URI')
        if not redirect_uri:
            return jsonify({'error': 'Configuration Error', 'message': 'OAuth redirect URI not configured'}), 500
        
        auth_url = OAuthService.get_google_authorization_url(redirect_uri)
        return redirect(auth_url)
        
    except Exception as e:
        logger.error(f"Error initiating Google OAuth: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal Server Error', 'message': 'An error occurred'}), 500


@auth_bp.route('/oauth/microsoft/authorize', methods=['GET'])
def microsoft_oauth_authorize():
    """
    Initiate Microsoft OAuth flow.
    
    Returns:
        Redirect to Microsoft OAuth authorization page
    """
    try:
        redirect_uri = current_app.config.get('OAUTH_REDIRECT_URI')
        if not redirect_uri:
            return jsonify({'error': 'Configuration Error', 'message': 'OAuth redirect URI not configured'}), 500
        
        auth_url = OAuthService.get_microsoft_authorization_url(redirect_uri)
        return redirect(auth_url)
        
    except Exception as e:
        logger.error(f"Error initiating Microsoft OAuth: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal Server Error', 'message': 'An error occurred'}), 500


@auth_bp.route('/oauth/callback', methods=['GET'])
def oauth_callback():
    """
    Handle OAuth callback from provider.
    
    Query parameters:
        code: Authorization code
        provider: OAuth provider ('google' or 'microsoft')
        
    Returns:
        JSON response with user data and tokens
    """
    try:
        code = request.args.get('code')
        provider = request.args.get('provider', 'google')
        state = request.args.get('state')  # Optional CSRF protection
        
        if not code:
            return jsonify({'error': 'Bad Request', 'message': 'Authorization code required'}), 400
        
        redirect_uri = current_app.config.get('OAUTH_REDIRECT_URI')
        
        # Exchange code for token and user info
        if provider == 'google':
            user_info, success, message = OAuthService.exchange_google_code(code, redirect_uri)
        elif provider == 'microsoft':
            user_info, success, message = OAuthService.exchange_microsoft_code(code, redirect_uri)
        else:
            return jsonify({'error': 'Bad Request', 'message': f'Unknown provider: {provider}'}), 400
        
        if not success or not user_info:
            return jsonify({'error': 'OAuth Failed', 'message': message}), 400
        
        # Extract user info
        email = user_info.get('email') or user_info.get('mail')  # Microsoft uses 'mail'
        first_name = user_info.get('given_name') or user_info.get('first_name', '').split()[0] if user_info.get('first_name') else ''
        last_name = user_info.get('family_name') or user_info.get('last_name', '').split()[-1] if user_info.get('last_name') else ''
        oauth_id = user_info.get('id') or user_info.get('sub')
        
        if not email or not oauth_id:
            return jsonify({'error': 'OAuth Failed', 'message': 'Incomplete user information from provider'}), 400
        
        # Create or update user
        access_token = user_info.get('access_token')  # Not typically in user_info, would need separate storage
        user, success, message = OAuthService.create_or_update_user_from_oauth(
            provider=provider,
            oauth_id=oauth_id,
            email=email,
            first_name=first_name or 'User',
            last_name=last_name or '',
            access_token=None  # OAuth token not typically returned in user_info
        )
        
        if not success or not user:
            return jsonify({'error': 'User Creation Failed', 'message': message}), 400
        
        # Login user
        login_user(user, remember=False)
        
        # Generate tokens
        tokens = AuthService.generate_jwt_tokens(user)
        
        logger.info(f"OAuth login successful: {email} via {provider}")
        
        return jsonify({
            'message': 'OAuth authentication successful',
            'user': user.to_dict(include_sensitive=False),
            'tokens': tokens
        }), 200
        
    except Exception as e:
        logger.error(f"Error handling OAuth callback: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal Server Error', 'message': 'An error occurred during OAuth'}), 500
