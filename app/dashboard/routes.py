"""Dashboard routes for Radar application."""

from flask import Blueprint, render_template, jsonify
from flask_jwt_extended import get_jwt_identity
from app.auth.decorators import requires_authentication
from app.companies.models import Company
from app.reports.models import Report
from app.extensions import db
import logging


logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('', methods=['GET'])
@requires_authentication
def dashboard():
    """Executive dashboard view."""
    try:
        user_id = get_jwt_identity()
        
        # Get user's companies and reports
        companies = Company.query.filter_by(user_id=user_id).all()
        reports = Report.query.filter_by(user_id=user_id).order_by(Report.generated_at.desc()).limit(10).all()
        
        return render_template(
            'dashboard/dashboard.html',
            companies=companies,
            reports=reports
        )
        
    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal Server Error', 'message': 'An error occurred'}), 500


@dashboard_bp.route('/api/data', methods=['GET'])
@requires_authentication
def dashboard_data():
    """Get dashboard data (JSON API)."""
    try:
        user_id = get_jwt_identity()
        
        companies = Company.query.filter_by(user_id=user_id).all()
        reports = Report.query.filter_by(user_id=user_id).order_by(Report.generated_at.desc()).limit(10).all()
        
        return jsonify({
            'companies': [c.to_dict() for c in companies],
            'reports': [r.to_dict() for r in reports]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal Server Error', 'message': 'An error occurred'}), 500
