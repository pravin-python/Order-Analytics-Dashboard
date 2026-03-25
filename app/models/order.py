"""Order models for persistent storage."""

from datetime import datetime, timezone
from app import db


class Order(db.Model):
    """Stores fetched order statistics and metadata."""
    __tablename__ = 'order'

    id = db.Column(db.Integer, primary_key=True)
    order_code = db.Column(db.String(100), unique=True, index=True)
    store_type = db.Column(db.String(10))  # PA, PI, MA, BL
    created_time = db.Column(db.DateTime)
    dispatch_time = db.Column(db.DateTime, nullable=True)
    shipping_hours = db.Column(db.Float, nullable=True)
    awb = db.Column(db.String(100), nullable=True)
    raw_data = db.Column(db.JSON, nullable=True)
    
    # Audit timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )


class OrderPackage(db.Model):
    """Stores individual package data per order."""
    __tablename__ = 'order_package'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    tracking_number = db.Column(db.String(100), index=True)
    dispatch_time = db.Column(db.DateTime, nullable=True)
    
    # Audit timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
