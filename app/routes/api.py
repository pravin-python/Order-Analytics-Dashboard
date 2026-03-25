"""API routes for AJAX calls."""

import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file, current_app
from flask_login import login_required
from app import db
from app.models.settings import Settings
from app.utils.encryption import encrypt_value, decrypt_value
from app.services.auth_service import AuthService
from app.services.order_service import OrderService
from app.services.task_manager import task_manager
from app.services.export_service import export_orders_to_excel

logger = logging.getLogger(__name__)
api_bp = Blueprint('api', __name__)

# In-memory storage for processed results (per-session)
_last_analytics = {}


def _get_services():
    """Initialize auth and order services from stored settings."""
    settings = Settings.query.filter_by(is_active=True).first()
    if not settings:
        return None, None, 'No API settings configured. Please configure settings first.'

    try:
        username = decrypt_value(settings.username)
        password = decrypt_value(settings.password)
    except Exception:
        return None, None, 'Failed to decrypt credentials. Please re-save settings.'

    auth_svc = AuthService(settings.api_base_url, username, password)
    order_svc = OrderService(settings.api_base_url, auth_svc)

    return auth_svc, order_svc, None


@api_bp.route('/test-connection', methods=['POST'])
@login_required
def test_connection():
    """Test OMS API connection with provided or stored credentials."""
    data = request.get_json() or {}

    base_url = data.get('api_base_url', '').strip()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not all([base_url, username, password]):
        # Try stored credentials
        settings = Settings.query.filter_by(is_active=True).first()
        if settings:
            base_url = base_url or settings.api_base_url
            username = username or decrypt_value(settings.username)
            password = password or decrypt_value(settings.password)

    if not all([base_url, username, password]):
        return jsonify({'success': False, 'message': 'Please provide API URL, username, and password.'}), 400

    auth_svc = AuthService(base_url, username, password)
    result = auth_svc.test_connection()

    # Update last tested time if using stored settings
    if result['success']:
        settings = Settings.query.filter_by(is_active=True).first()
        if settings:
            settings.last_tested = datetime.utcnow()
            settings.last_test_success = True
            db.session.commit()

    return jsonify(result)


@api_bp.route('/save-settings', methods=['POST'])
@login_required
def save_settings():
    """Save OMS API credentials (encrypted)."""
    data = request.get_json() or {}

    base_url = data.get('api_base_url', '').strip()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not all([base_url, username, password]):
        return jsonify({'success': False, 'message': 'All fields are required.'}), 400

    try:
        encrypted_user = encrypt_value(username)
        encrypted_pass = encrypt_value(password)

        # Deactivate existing settings
        Settings.query.update({Settings.is_active: False})

        # Create new settings
        settings = Settings(
            api_base_url=base_url,
            username=encrypted_user,
            password=encrypted_pass,
            is_active=True
        )
        db.session.add(settings)
        db.session.commit()

        logger.info(f'Settings saved successfully for {base_url}')
        return jsonify({
            'success': True,
            'message': 'Settings saved successfully.',
            'settings': settings.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error saving settings: {e}')
        return jsonify({'success': False, 'message': f'Failed to save: {str(e)}'}), 500


@api_bp.route('/get-settings', methods=['GET'])
@login_required
def get_settings():
    """Get current saved settings (masked)."""
    settings = Settings.query.filter_by(is_active=True).first()
    if not settings:
        return jsonify({'exists': False})

    return jsonify({'exists': True, 'settings': settings.to_dict()})


@api_bp.route('/settings', methods=['DELETE'])
@login_required
def clear_settings():
    """Clear all stored settings."""
    try:
        Settings.query.delete()
        db.session.commit()
        return jsonify({'success': True, 'message': 'Settings cleared.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


_last_dates = {'from': '', 'to': ''}

@api_bp.route('/fetch-orders', methods=['POST'])
@login_required
def fetch_orders():
    """Trigger background order fetching and DB syncing."""
    data = request.get_json() or {}
    from_date = data.get('from_date', '')
    to_date = data.get('to_date', '')

    if not from_date or not to_date:
        return jsonify({'success': False, 'message': 'Please select both date ranges.'}), 400

    _last_dates['from'] = from_date
    _last_dates['to'] = to_date

    auth_svc, order_svc, error = _get_services()
    if error:
        return jsonify({'success': False, 'message': error}), 400

    app = current_app._get_current_object()  # Capture before thread

    def background_fetch(task_id, cancel_flag):
        """Background task for fetching and syncing orders to DB."""
        with app.app_context():
            task_manager.update_progress(task_id, 10, 'Authenticating...')

            if cancel_flag.is_set(): return None

            task_manager.update_progress(task_id, 20, 'Fetching orders...')
            orders = order_svc.fetch_orders(from_date, to_date)

            if cancel_flag.is_set(): return None

            task_manager.update_progress(task_id, 20, f'Fetching order details and persisting DB ({len(orders)} found)...')

            def _progress(completed, total):
                percent_done = 20 + int((completed / total) * 70) if total > 0 else 90
                task_manager.update_progress(task_id, percent_done, f'Processing and syncing orders ({completed}/{total})...')

            order_svc.process_orders(orders, on_progress=_progress)

            if cancel_flag.is_set(): return None

            task_manager.update_progress(task_id, 90, 'Finalizing Database Sync...')
            task_manager.update_progress(task_id, 100, 'Tasks Complete.')
            return {'status': 'done'}

    task_id = task_manager.submit(background_fetch)
    return jsonify({'success': True, 'task_id': task_id, 'message': 'Order sync started.'})


@api_bp.route('/orders', methods=['GET'])
@login_required
def get_orders():
    """Fetch orders directly from Database for the dashboard."""
    from_date = request.args.get('from_date', _last_dates['from'])
    to_date = request.args.get('to_date', _last_dates['to'])
    
    if not from_date or not to_date:
        return jsonify({'success': False, 'message': 'Date range required.'}), 400
        
    auth_svc, order_svc, error = _get_services()
    if error or not order_svc:
        return jsonify({'success': False, 'message': error or 'Service unavailable.'}), 400
        
    try:
        analytics = order_svc.get_analytics_from_db(from_date, to_date)
        return jsonify({'success': True, 'data': analytics})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/orders/status', methods=['GET'])
@login_required
def order_status():
    """Poll the status of a background order fetch task."""
    task_id = request.args.get('task_id', '')
    if not task_id:
        return jsonify({'status': 'error', 'message': 'No task_id provided.'}), 400

    status = task_manager.get_status(task_id)
    return jsonify(status)


@api_bp.route('/orders/cancel', methods=['POST'])
@login_required
def cancel_orders():
    """Cancel a running background task."""
    data = request.get_json() or {}
    task_id = data.get('task_id', '')
    if task_id:
        task_manager.cancel(task_id)
        return jsonify({'success': True, 'message': 'Cancel signal sent.'})
    return jsonify({'success': False, 'message': 'No task_id provided.'}), 400


@api_bp.route('/order/<code>', methods=['GET'])
@login_required
def get_order_detail(code):
    """Fetch detailed information for a specific order."""
    auth_svc, order_svc, error = _get_services()
    if error:
        return jsonify({'success': False, 'message': error}), 400

    try:
        detail = order_svc.fetch_order_detail(code)
        return jsonify({'success': True, 'data': detail})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/report', methods=['GET'])
@login_required
def get_report():
    """Get the latest processed analytics data from DB."""
    if not _last_dates['from'] or not _last_dates['to']:
         return jsonify({'success': False, 'message': 'No date context available. Please sync or load orders.'}), 404
         
    auth_svc, order_svc, error = _get_services()
    if error or not order_svc:
        return jsonify({'success': False, 'message': error or 'Service unavailable.'}), 400
        
    try:
        analytics = order_svc.get_analytics_from_db(_last_dates['from'], _last_dates['to'])
        return jsonify({'success': True, 'data': analytics})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/export', methods=['GET'])
@login_required
def export_excel():
    """Export the latest analytics data to Excel."""
    if not _last_dates['from'] or not _last_dates['to']:
         return jsonify({'success': False, 'message': 'No date context available. Please sync or load orders.'}), 404
         
    auth_svc, order_svc, error = _get_services()
    if error or not order_svc:
        return jsonify({'success': False, 'message': error or 'Service unavailable.'}), 400

    try:
        analytics = order_svc.get_analytics_from_db(_last_dates['from'], _last_dates['to'])
        output = export_orders_to_excel(analytics)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'orderpulse_report_{timestamp}.xlsx'
        )
    except Exception as e:
        logger.error(f'Export error: {e}')
        return jsonify({'success': False, 'message': str(e)}), 500
