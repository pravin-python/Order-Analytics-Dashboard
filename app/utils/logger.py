"""Logging configuration module."""

import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime


def setup_logging(app):
    """Configure application logging with file and console handlers."""
    log_dir = app.config.get('LOG_DIR', 'logs')
    os.makedirs(log_dir, exist_ok=True)

    log_filename = f'orderpulse_{datetime.now().strftime("%Y-%m-%d")}.log'
    log_path = os.path.join(log_dir, log_filename)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_path, maxBytes=10 * 1024 * 1024, backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if app.debug else logging.INFO)
    console_handler.setFormatter(logging.Formatter(
        '%(levelname)s - %(message)s'
    ))

    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.DEBUG if app.debug else logging.INFO)

    app.logger.info(f'Logging initialized. File: {log_path}')
