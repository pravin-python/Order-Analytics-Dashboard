"""Authentication service — business logic for user auth operations."""

import logging
from flask import current_app
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from app import db
from app.models.user import User

logger = logging.getLogger(__name__)


class UserAuthService:
    """Handles registration, authentication, password reset, and profile updates."""

    # --- Registration ---
    @staticmethod
    def register_user(name, email, password):
        """Create a new user. Returns (user, error_message)."""
        if not name or not email or not password:
            return None, 'Name, email, and password are required.'

        if len(password) < 6:
            return None, 'Password must be at least 6 characters.'

        existing = User.query.filter_by(email=email.lower().strip()).first()
        if existing:
            return None, 'An account with this email already exists.'

        try:
            user = User(
                name=name.strip(),
                email=email.lower().strip()
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            logger.info(f'New user registered: {user.email}')
            return user, None
        except Exception as e:
            db.session.rollback()
            logger.error(f'Registration error: {e}')
            return None, 'Registration failed. Please try again.'

    # --- Authentication ---
    @staticmethod
    def authenticate(email, password):
        """Validate credentials. Returns (user, error_message)."""
        if not email or not password:
            return None, 'Email and password are required.'

        user = User.query.filter_by(email=email.lower().strip()).first()
        if not user:
            return None, 'Invalid email or password.'

        if not user.is_active:
            return None, 'This account has been deactivated.'

        if not user.check_password(password):
            return None, 'Invalid email or password.'

        logger.info(f'User authenticated: {user.email}')
        return user, None

    # --- Password Reset ---
    @staticmethod
    def generate_reset_token(email):
        """Generate a time-limited password reset token. Returns (token, error)."""
        user = User.query.filter_by(email=email.lower().strip()).first()
        if not user:
            # Don't reveal whether email exists
            return None, None

        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        token = serializer.dumps(user.email, salt='password-reset')
        logger.info(f'Password reset token generated for {user.email}: {token}')
        return token, None

    @staticmethod
    def reset_password(token, new_password):
        """Validate token and set new password. Returns (success, error)."""
        if not new_password or len(new_password) < 6:
            return False, 'Password must be at least 6 characters.'

        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            email = serializer.loads(token, salt='password-reset', max_age=3600)
        except SignatureExpired:
            return False, 'Reset link has expired. Please request a new one.'
        except BadSignature:
            return False, 'Invalid reset link.'

        user = User.query.filter_by(email=email).first()
        if not user:
            return False, 'User not found.'

        user.set_password(new_password)
        db.session.commit()
        logger.info(f'Password reset successful for {user.email}')
        return True, None

    # --- Profile ---
    @staticmethod
    def update_profile(user, name=None, email=None):
        """Update user profile fields. Returns (success, error)."""
        try:
            if name:
                user.name = name.strip()
            if email:
                new_email = email.lower().strip()
                if new_email != user.email:
                    existing = User.query.filter_by(email=new_email).first()
                    if existing:
                        return False, 'This email is already in use.'
                    user.email = new_email

            db.session.commit()
            logger.info(f'Profile updated for {user.email}')
            return True, None
        except Exception as e:
            db.session.rollback()
            logger.error(f'Profile update error: {e}')
            return False, 'Failed to update profile.'

    # --- Change Password ---
    @staticmethod
    def change_password(user, old_password, new_password):
        """Change password after validating old one. Returns (success, error)."""
        if not user.check_password(old_password):
            return False, 'Current password is incorrect.'

        if len(new_password) < 6:
            return False, 'New password must be at least 6 characters.'

        user.set_password(new_password)
        db.session.commit()
        logger.info(f'Password changed for {user.email}')
        return True, None
