"""Application configuration module."""

import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def get_database_uri():
    db_type = os.environ.get("DB_TYPE", "sqlite")

    if db_type == "sqlite":
        return f"sqlite:///{os.path.join(BASE_DIR, 'instance', os.environ.get('SQLITE_DB', 'orderpulse.db'))}"
    elif db_type in ["mysql", "mariadb"]:
        return f"mysql+pymysql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}@{os.environ.get('DB_HOST')}:{os.environ.get('DB_PORT', '3306')}/{os.environ.get('DB_NAME')}"
    elif db_type == "postgres" or db_type == "postgresql":
        return f"postgresql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}@{os.environ.get('DB_HOST')}:{os.environ.get('DB_PORT', '5432')}/{os.environ.get('DB_NAME')}"
    else:
        raise Exception("Invalid DB_TYPE")

class Config:
    """Base configuration."""

    SECRET_KEY = os.environ.get('SECRET_KEY', 'orderpulse-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Cache settings
    CACHE_TTL = int(os.environ.get('CACHE_TTL', 300))  # 5 minutes
    TOKEN_CACHE_TTL = int(os.environ.get('TOKEN_CACHE_TTL', 3500))  # ~58 minutes

    # Background task settings
    MAX_WORKERS = int(os.environ.get('MAX_WORKERS', 5))
    BATCH_SIZE = int(os.environ.get('BATCH_SIZE', 50))

    # Order prefixes for multi-store filtering
    STORE_PREFIXES = ['PA', 'PI', 'MA', 'BL']

    # Session / Cookie Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_DURATION = 60 * 60 * 24 * 7   # 7 days in seconds

    # Logging
    LOG_DIR = os.path.join(BASE_DIR, 'logs')


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False


config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
