"""Main page routes."""

from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def dashboard():
    """Render the main dashboard page."""
    return render_template('dashboard.html')


@main_bp.route('/settings')
def settings():
    """Render the settings/credentials page."""
    return render_template('settings.html')
