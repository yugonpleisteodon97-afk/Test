"""Report routes for Radar application."""

from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import get_jwt_identity
from app.extensions import db
from app.auth.decorators import requires_authentication
from app.reports.models import Report, ReportType
from app.reports.generator import ReportGenerator
from app.config import Config
from pathlib import Path
import logging
from datetime import datetime


logger = logging.getLogger(__name__)

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/generate', methods=['POST'])
@requires_authentication
def generate_report():
    """Generate on-demand report. TODO: Implement full generation logic."""
    try:
        data = request.get_json() or {}
        user_id = get_jwt_identity()
        company_id = data.get('company_id')
        
        if not company_id:
            return jsonify({'error': 'Bad Request', 'message': 'company_id required'}), 400
        
        # Generate report
        generator = ReportGenerator(Path(Config.REPORT_OUTPUT_DIR))
        report = generator.generate_report(
            company_id=company_id,
            user_id=user_id,
            report_type=ReportType.ON_DEMAND
        )
        
        if not report:
            return jsonify({'error': 'Generation Failed', 'message': 'Failed to generate report'}), 500
        
        db.session.add(report)
        db.session.commit()
        
        return jsonify({
            'message': 'Report generated successfully',
            'report': report.to_dict(include_full=True)
        }), 201
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal Server Error', 'message': 'An error occurred'}), 500


@reports_bp.route('/<report_id>', methods=['GET'])
@requires_authentication
def get_report(report_id):
    """Get report metadata."""
    try:
        user_id = get_jwt_identity()
        report = Report.query.filter_by(id=report_id, user_id=user_id).first()
        
        if not report:
            return jsonify({'error': 'Not Found', 'message': 'Report not found'}), 404
        
        return jsonify({
            'report': report.to_dict(include_full=True)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting report: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal Server Error', 'message': 'An error occurred'}), 500


@reports_bp.route('/<report_id>/download', methods=['GET'])
@requires_authentication
def download_report(report_id):
    """Download report PDF file."""
    try:
        user_id = get_jwt_identity()
        report = Report.query.filter_by(id=report_id, user_id=user_id).first()
        
        if not report or not report.pdf_file_path:
            return jsonify({'error': 'Not Found', 'message': 'Report not found'}), 404
        
        pdf_path = Path(report.pdf_file_path)
        if not pdf_path.exists():
            return jsonify({'error': 'Not Found', 'message': 'Report file not found'}), 404
        
        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"report_{report_id}.pdf"
        )
        
    except Exception as e:
        logger.error(f"Error downloading report: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal Server Error', 'message': 'An error occurred'}), 500
