"""Authentication routes — pages and AJAX API endpoints."""

import logging
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from app.services.user_auth_service import UserAuthService

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)


# ─────────────────────────────────────
# Page Routes (render templates)
# ─────────────────────────────────────

@auth_bp.route('/auth/login')
def login():
    """Render login page."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('auth/login.html')


@auth_bp.route('/auth/register')
def register():
    """Render register page."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('auth/register.html')


@auth_bp.route('/auth/forgot-password')
def forgot_password():
    """Render forgot password page."""
    return render_template('auth/forgot_password.html')


@auth_bp.route('/auth/reset-password/<token>')
def reset_password_page(token):
    """Render reset password page."""
    return render_template('auth/reset_password.html', token=token)


@auth_bp.route('/auth/profile')
@login_required
def profile():
    """Render profile page."""
    return render_template('user/profile.html')


@auth_bp.route('/auth/change-password')
@login_required
def change_password_page():
    """Render change password page."""
    return render_template('user/change_password.html')


# ─────────────────────────────────────
# AJAX API Endpoints
# ─────────────────────────────────────

@auth_bp.route('/api/auth/login', methods=['POST'])
def api_login():
    """Authenticate user and create session."""
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    password = data.get('password', '')
    remember = data.get('remember', False)

    user, error = UserAuthService.authenticate(email, password)
    if error:
        return jsonify({'success': False, 'message': error}), 401

    login_user(user, remember=remember)
    logger.info(f'User logged in: {user.email}')
    return jsonify({
        'success': True,
        'message': 'Login successful.',
        'user': user.to_dict()
    })


@auth_bp.route('/api/auth/logout', methods=['POST'])
@login_required
def api_logout():
    """Logout user and clear session."""
    logger.info(f'User logged out: {current_user.email}')
    logout_user()
    return jsonify({'success': True, 'message': 'Logged out successfully.'})


@auth_bp.route('/api/auth/register', methods=['POST'])
def api_register():
    """Register a new user."""
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    confirm = data.get('confirm_password', '')

    if password != confirm:
        return jsonify({'success': False, 'message': 'Passwords do not match.'}), 400

    user, error = UserAuthService.register_user(name, email, password)
    if error:
        return jsonify({'success': False, 'message': error}), 400

    return jsonify({'success': True, 'message': 'Registration successful. Please login.'})


@auth_bp.route('/api/auth/forgot-password', methods=['POST'])
def api_forgot_password():
    """Generate password reset token."""
    data = request.get_json() or {}
    email = data.get('email', '').strip()

    if not email:
        return jsonify({'success': False, 'message': 'Email is required.'}), 400

    token, _ = UserAuthService.generate_reset_token(email)

    # Always return success to avoid email enumeration
    msg = 'If an account with that email exists, a reset link has been generated. Check the application logs.'
    if token:
        logger.info(f'[DEV] Password reset URL: /auth/reset-password/{token}')

    return jsonify({'success': True, 'message': msg})


@auth_bp.route('/api/auth/reset-password', methods=['POST'])
def api_reset_password():
    """Reset password using token."""
    data = request.get_json() or {}
    token = data.get('token', '')
    new_password = data.get('new_password', '')
    confirm = data.get('confirm_password', '')

    if new_password != confirm:
        return jsonify({'success': False, 'message': 'Passwords do not match.'}), 400

    success, error = UserAuthService.reset_password(token, new_password)
    if not success:
        return jsonify({'success': False, 'message': error}), 400

    return jsonify({'success': True, 'message': 'Password reset successful. Please login.'})


@auth_bp.route('/api/auth/profile', methods=['GET'])
@login_required
def api_get_profile():
    """Get current user profile."""
    return jsonify({'success': True, 'user': current_user.to_dict()})


@auth_bp.route('/api/auth/profile', methods=['PUT'])
@login_required
def api_update_profile():
    """Update current user profile."""
    data = request.get_json() or {}
    name = data.get('name')
    email = data.get('email')

    success, error = UserAuthService.update_profile(current_user, name, email)
    if not success:
        return jsonify({'success': False, 'message': error}), 400

    return jsonify({
        'success': True,
        'message': 'Profile updated.',
        'user': current_user.to_dict()
    })


@auth_bp.route('/api/auth/change-password', methods=['POST'])
@login_required
def api_change_password():
    """Change current user password."""
    data = request.get_json() or {}
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')
    confirm = data.get('confirm_password', '')

    if new_password != confirm:
        return jsonify({'success': False, 'message': 'New passwords do not match.'}), 400

    success, error = UserAuthService.change_password(current_user, old_password, new_password)
    if not success:
        return jsonify({'success': False, 'message': error}), 400

    return jsonify({'success': True, 'message': 'Password changed successfully.'})
