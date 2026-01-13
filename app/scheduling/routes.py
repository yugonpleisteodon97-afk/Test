"""Scheduling routes for Radar application."""

from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity
from app.auth.decorators import requires_authentication, requires_admin
from app.scheduling.tasks import generate_quarterly_report, check_alerts, collect_intelligence
import logging


logger = logging.getLogger(__name__)

scheduling_bp = Blueprint('scheduling', __name__)


@scheduling_bp.route('/trigger/quarterly-report', methods=['POST'])
@requires_authentication
@requires_admin
def trigger_quarterly_report():
    """Trigger quarterly report generation (admin only)."""
    try:
        from flask import request
        data = request.get_json() or {}
        company_id = data.get('company_id')
        user_id = get_jwt_identity()
        
        if not company_id:
            return jsonify({'error': 'Bad Request', 'message': 'company_id required'}), 400
        
        # Trigger async task
        task = generate_quarterly_report.delay(company_id, user_id)
        
        return jsonify({
            'message': 'Quarterly report generation triggered',
            'task_id': task.id
        }), 202
        
    except Exception as e:
        logger.error(f"Error triggering quarterly report: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal Server Error', 'message': 'An error occurred'}), 500
