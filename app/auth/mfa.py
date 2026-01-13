"""
Multi-factor authentication (MFA) for Radar application.

Implements TOTP-based MFA using pyotp with QR code generation
and backup codes for account recovery.
"""

from app.extensions import db
from app.auth.models import User
from app.utils.security import get_security_manager
import pyotp
import qrcode
import io
import base64
import secrets
import hashlib
from typing import Tuple, Optional, List, Dict, Any
import logging


logger = logging.getLogger(__name__)


class MFAService:
    """Service for MFA operations."""
    
    @staticmethod
    def generate_mfa_secret() -> str:
        """
        Generate new TOTP secret for user.
        
        Returns:
            Base32-encoded TOTP secret
        """
        return pyotp.random_base32()
    
    @staticmethod
    def generate_qr_code(secret: str, email: str, issuer: str = 'Radar') -> str:
        """
        Generate QR code for MFA setup.
        
        Args:
            secret: TOTP secret
            email: User email address
            issuer: Issuer name (default: 'Radar')
            
        Returns:
            Base64-encoded PNG image data
        """
        # Create TOTP URI
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=email,
            issuer_name=issuer
        )
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4
        )
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_data = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_data}"
    
    @staticmethod
    def enable_mfa(user: User, secret: str, verification_code: str) -> Tuple[bool, str]:
        """
        Enable MFA for user after verification.
        
        Args:
            user: User object
            secret: TOTP secret
            verification_code: 6-digit verification code
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Verify code
            totp = pyotp.TOTP(secret)
            if not totp.verify(verification_code, valid_window=1):
                return False, "Invalid verification code"
            
            # Encrypt secret
            security_manager = get_security_manager()
            encrypted_secret = security_manager.encrypt(secret)
            
            # Generate backup codes
            backup_codes = MFAService.generate_backup_codes()
            hashed_codes = [hashlib.sha256(code.encode()).hexdigest() for code in backup_codes]
            
            # Store encrypted secret and backup codes
            user.mfa_secret = encrypted_secret
            user.mfa_enabled = True
            user.backup_codes = ','.join(hashed_codes)  # Store hashed codes
            
            db.session.commit()
            
            logger.info(f"MFA enabled for user: {user.email}")
            
            return True, backup_codes  # Return plaintext codes once for user to save
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error enabling MFA: {str(e)}", exc_info=True)
            return False, "An error occurred while enabling MFA"
    
    @staticmethod
    def verify_mfa_code(user: User, code: str) -> bool:
        """
        Verify MFA code for user.
        
        Args:
            user: User object
            code: 6-digit TOTP code or backup code
            
        Returns:
            True if code is valid, False otherwise
        """
        try:
            # Check if MFA is enabled
            if not user.mfa_enabled or not user.mfa_secret:
                return False
            
            # Decrypt secret
            security_manager = get_security_manager()
            secret = security_manager.decrypt(user.mfa_secret)
            
            # Try TOTP code first
            totp = pyotp.TOTP(secret)
            if totp.verify(code, valid_window=1):
                return True
            
            # Try backup codes
            if user.backup_codes:
                hashed_input = hashlib.sha256(code.encode()).hexdigest()
                backup_codes = user.backup_codes.split(',')
                if hashed_input in backup_codes:
                    # Remove used backup code
                    backup_codes.remove(hashed_input)
                    user.backup_codes = ','.join(backup_codes) if backup_codes else None
                    db.session.commit()
                    logger.info(f"Backup code used for user: {user.email}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error verifying MFA code: {str(e)}", exc_info=True)
            return False
    
    @staticmethod
    def disable_mfa(user: User) -> Tuple[bool, str]:
        """
        Disable MFA for user.
        
        Args:
            user: User object
            
        Returns:
            Tuple of (success, message)
        """
        try:
            user.mfa_enabled = False
            user.mfa_secret = None
            user.backup_codes = None
            
            db.session.commit()
            
            logger.info(f"MFA disabled for user: {user.email}")
            return True, "MFA disabled successfully"
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error disabling MFA: {str(e)}", exc_info=True)
            return False, "An error occurred while disabling MFA"
    
    @staticmethod
    def generate_backup_codes(count: int = 10) -> List[str]:
        """
        Generate backup codes for MFA recovery.
        
        Args:
            count: Number of backup codes to generate (default: 10)
            
        Returns:
            List of backup codes (8-character alphanumeric)
        """
        codes = []
        for _ in range(count):
            code = secrets.token_hex(4).upper()  # 8-character code
            codes.append(code)
        return codes
    
    @staticmethod
    def regenerate_backup_codes(user: User) -> Tuple[bool, List[str], str]:
        """
        Regenerate backup codes for user.
        
        Args:
            user: User object
            
        Returns:
            Tuple of (success, backup_codes, message)
        """
        try:
            if not user.mfa_enabled:
                return False, [], "MFA is not enabled"
            
            # Generate new backup codes
            backup_codes = MFAService.generate_backup_codes()
            hashed_codes = [hashlib.sha256(code.encode()).hexdigest() for code in backup_codes]
            
            # Store hashed codes
            user.backup_codes = ','.join(hashed_codes)
            db.session.commit()
            
            logger.info(f"Backup codes regenerated for user: {user.email}")
            return True, backup_codes, "Backup codes regenerated successfully"
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error regenerating backup codes: {str(e)}", exc_info=True)
            return False, [], "An error occurred while regenerating backup codes"
