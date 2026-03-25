"""Settings model for API credential storage."""

from datetime import datetime, timezone
from app import db


class Settings(db.Model):
    """Stores OMS API credentials (encrypted) and connection metadata."""

    __tablename__ = 'settings'

    id = db.Column(db.Integer, primary_key=True)
    api_base_url = db.Column(db.String(500), nullable=False)
    username = db.Column(db.Text, nullable=False)  # Encrypted
    password = db.Column(db.Text, nullable=False)  # Encrypted
    is_active = db.Column(db.Boolean, default=True)
    last_tested = db.Column(db.DateTime, nullable=True)
    last_test_success = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self):
        """Return a safe dictionary representation (no credentials)."""
        from app.utils.encryption import decrypt_value
        try:
            plain_username = decrypt_value(self.username)
            masked = self._mask(plain_username)
        except Exception:
            masked = '***'

        return {
            'id': self.id,
            'api_base_url': self.api_base_url,
            'username_masked': masked,
            'is_active': self.is_active,
            'last_tested': self.last_tested.isoformat() if self.last_tested else None,
            'last_test_success': self.last_test_success,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @staticmethod
    def _mask(value):
        """Mask a string, showing only first 3 and last 3 characters."""
        if not value or len(value) < 5:
            return '***'
        return value[:3] + '*' * min(len(value) - 6, 6) + value[-3:]

    def __repr__(self):
        return f'<Settings id={self.id} url={self.api_base_url}>'
