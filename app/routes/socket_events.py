"""SocketIO event handlers for real-time updates."""

import logging
from app import socketio
from flask_socketio import emit

logger = logging.getLogger(__name__)


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info('Client connected to SocketIO.')
    emit('connected', {'status': 'connected', 'message': 'Real-time updates enabled.'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info('Client disconnected from SocketIO.')


@socketio.on('ping_server')
def handle_ping():
    """Respond to a ping from the client."""
    emit('pong_server', {'status': 'alive'})
