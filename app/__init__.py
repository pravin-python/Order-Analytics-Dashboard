"""Application factory module."""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

from config import config_map

db = SQLAlchemy()
socketio = SocketIO(cors_allowed_origins="*", async_mode='threading')


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

    # Configure logging
    from app.utils.logger import setup_logging
    setup_logging(app)

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    # Register SocketIO events
    from app.routes import socket_events  # noqa: F401

    # Database commands
    @app.cli.command('init-db')
    def init_db_command():
        """Initialize the database by creating all tables."""
        from app.models import settings, order
        db.create_all()
        print('Database tables created successfully.')

    return app
