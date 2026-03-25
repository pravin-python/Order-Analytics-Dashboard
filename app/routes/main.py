"""Main page routes."""

from flask import Blueprint, render_template
from flask_login import login_required

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@login_required
def dashboard():
    """Render the main dashboard page."""
    return render_template('dashboard.html')


@main_bp.route('/settings')
@login_required
def settings():
    """Render the settings/credentials page."""
    return render_template('settings.html')
