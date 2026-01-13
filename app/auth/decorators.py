"""
Authentication and authorization decorators for Radar application.

Provides role-based access control decorators for route protection.
"""

from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from flask_login import current_user
from app.auth.models import UserRole
from typing import List, Callable, Any
import logging


logger = logging.getLogger(__name__)


def requires_role(*roles: UserRole):
    """
    Decorator to require specific role(s) for route access.
    
    Usage:
        @auth_bp.route('/ceo-only')
        @requires_role(UserRole.CEO, UserRole.ADMIN)
        def ceo_only_endpoint():
            ...
    
    Args:
        *roles: One or more UserRole enum values
        
    Returns:
        Decorator function
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            # Verify JWT token is present
            try:
                verify_jwt_in_request()
                claims = get_jwt()
                user_role = claims.get('role')
            except Exception as e:
                logger.warning(f"JWT verification failed: {str(e)}")
                return jsonify({
                    'error': 'Unauthorized',
                    'message': 'Authentication required'
                }), 401
            
            # Check if user has required role
            if user_role not in [role.value for role in roles]:
                logger.warning(f"Access denied for role {user_role} to {request.endpoint}")
                return jsonify({
                    'error': 'Forbidden',
                    'message': f'Insufficient permissions. Required roles: {[r.value for r in roles]}'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


def requires_any_role(*roles: UserRole):
    """
    Decorator to require any one of the specified roles.
    
    Usage:
        @auth_bp.route('/executive-only')
        @requires_any_role(UserRole.CEO, UserRole.CFO)
        def executive_endpoint():
            ...
    
    Args:
        *roles: One or more UserRole enum values
        
    Returns:
        Decorator function
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            try:
                verify_jwt_in_request()
                claims = get_jwt()
                user_role = claims.get('role')
            except Exception as e:
                logger.warning(f"JWT verification failed: {str(e)}")
                return jsonify({
                    'error': 'Unauthorized',
                    'message': 'Authentication required'
                }), 401
            
            # Check if user has any of the required roles
            if user_role not in [role.value for role in roles]:
                logger.warning(f"Access denied for role {user_role} to {request.endpoint}")
                return jsonify({
                    'error': 'Forbidden',
                    'message': f'Insufficient permissions. Requires one of: {[r.value for r in roles]}'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


def requires_admin(f: Callable) -> Callable:
    """
    Decorator to require admin role.
    
    Usage:
        @auth_bp.route('/admin-only')
        @requires_admin
        def admin_endpoint():
            ...
    
    Args:
        f: Route function to decorate
        
    Returns:
        Decorated function
    """
    return requires_role(UserRole.ADMIN)(f)


def requires_authentication(f: Callable) -> Callable:
    """
    Decorator to require authentication (any valid user).
    
    Usage:
        @auth_bp.route('/protected')
        @requires_authentication
        def protected_endpoint():
            ...
    
    Args:
        f: Route function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        try:
            verify_jwt_in_request()
        except Exception as e:
            logger.warning(f"JWT verification failed: {str(e)}")
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Authentication required'
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function


def optional_authentication(f: Callable) -> Callable:
    """
    Decorator to optionally allow authentication (doesn't fail if not authenticated).
    
    Usage:
        @auth_bp.route('/public-or-private')
        @optional_authentication
        def flexible_endpoint():
            ...
    
    Args:
        f: Route function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        try:
            verify_jwt_in_request()
        except Exception:
            # Authentication is optional, continue without it
            pass
        
        return f(*args, **kwargs)
    
    return decorated_function
