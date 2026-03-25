"""Application factory module."""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

from config import config_map

db = SQLAlchemy()
socketio = SocketIO(cors_allowed_origins="*", async_mode='threading')
login_manager = LoginManager()
bcrypt = Bcrypt()


def create_app(config_name=None):
    """Create and configure the Flask application."""
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')

    app = Flask(__name__)
    app.config.from_object(config_map[config_name])

    # Ensure instance and log directories exist
    os.makedirs(os.path.join(app.instance_path), exist_ok=True)
    os.makedirs(app.config.get('LOG_DIR', 'logs'), exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    socketio.init_app(app)
    bcrypt.init_app(app)

    # Flask-Login setup
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import request, jsonify, redirect, url_for
        # Return JSON for AJAX requests, redirect for page requests
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Authentication required.'}), 401
        return redirect(url_for('auth.login'))

    # Configure logging
    from app.utils.logger import setup_logging
    setup_logging(app)

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.api import api_bp
    from app.routes.auth import auth_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp)

    # Register SocketIO events
    from app.routes import socket_events  # noqa: F401

    # Database commands
    @app.cli.command('init-db')
    def init_db_command():
        """Initialize the database by creating all tables and default admin."""
        from app.models import settings, order
        from app.models.user import User
        db.create_all()
        print('Database tables created successfully.')

        # Create default admin user if not exists
        admin = User.query.filter_by(email='admin@orderpulse.com').first()
        if not admin:
            admin = User(name='Admin', email='admin@orderpulse.com')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print('Default admin user created: admin@orderpulse.com / admin123')
        else:
            print('Admin user already exists.')

    return app
