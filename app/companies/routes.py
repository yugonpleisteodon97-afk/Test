"""
Company and competitor routes for Radar application.

Handles company onboarding, competitor discovery, and management.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from app.extensions import db, limiter
from app.auth.decorators import requires_authentication
from app.companies.models import Company, Competitor, TrackingConfig, ReportFrequency
from app.companies.services import CompanyService, CompetitorDiscoveryService
from app.utils.validators import ValidationError
import logging


logger = logging.getLogger(__name__)

companies_bp = Blueprint('companies', __name__)


@companies_bp.route('', methods=['POST'])
@requires_authentication
@limiter.limit("10 per hour")
def create_company():
    """
    Create company from website URL.
    
    Request body:
        {
            "website_url": "https://example.com",
            "name": "Example Company"  # Optional
        }
    
    Returns:
        JSON response with company data
    """
    try:
        data = request.get_json()
        if not data or 'website_url' not in data:
            return jsonify({'error': 'Bad Request', 'message': 'website_url required'}), 400
        
        user_id = get_jwt_identity()
        company, success, message = CompanyService.create_company(
            user_id=user_id,
            website_url=data['website_url'],
            name=data.get('name')
        )
        
        if not success or not company:
            return jsonify({'error': 'Creation Failed', 'message': message}), 400
        
        return jsonify({
            'message': message,
            'company': company.to_dict()
        }), 201
        
    except ValidationError as e:
        return jsonify({'error': 'Validation Error', 'message': str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating company: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal Server Error', 'message': 'An error occurred'}), 500


@companies_bp.route('', methods=['GET'])
@requires_authentication
def get_companies():
    """Get all companies for current user."""
    try:
        user_id = get_jwt_identity()
        companies = Company.query.filter_by(user_id=user_id).all()
        
        return jsonify({
            'companies': [company.to_dict() for company in companies]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting companies: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal Server Error', 'message': 'An error occurred'}), 500


@companies_bp.route('/<company_id>/competitors/discover', methods=['POST'])
@requires_authentication
@limiter.limit("5 per hour")
def discover_competitors(company_id):
    """
    Discover competitors for a company.
    
    Returns:
        JSON response with suggested competitors
    """
    try:
        user_id = get_jwt_identity()
        company = Company.query.filter_by(id=company_id, user_id=user_id).first()
        
        if not company:
            return jsonify({'error': 'Not Found', 'message': 'Company not found'}), 404
        
        # Discover competitors
        competitors = CompetitorDiscoveryService.discover_competitors(company, max_results=5)
        
        # Create competitor records (pending approval)
        created_competitors = []
        for comp_data in competitors:
            competitor, success, message = CompetitorDiscoveryService.create_competitor(
                company_id=company_id,
                name=comp_data.get('name'),
                website_url=comp_data.get('website_url'),
                discovery_rationale=comp_data.get('discovery_rationale'),
                confidence_score=comp_data.get('confidence_score', 0),
                discovery_source=comp_data.get('discovery_source', 'auto')
            )
            if success and competitor:
                created_competitors.append(competitor.to_dict())
        
        logger.info(f"Competitor discovery completed for company: {company.name}")
        
        return jsonify({
            'message': f'Found {len(created_competitors)} potential competitors',
            'competitors': created_competitors
        }), 200
        
    except Exception as e:
        logger.error(f"Error discovering competitors: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal Server Error', 'message': 'An error occurred'}), 500


@companies_bp.route('/<company_id>/competitors', methods=['GET'])
@requires_authentication
def get_competitors(company_id):
    """Get all competitors for a company."""
    try:
        user_id = get_jwt_identity()
        company = Company.query.filter_by(id=company_id, user_id=user_id).first()
        
        if not company:
            return jsonify({'error': 'Not Found', 'message': 'Company not found'}), 404
        
        competitors = Competitor.query.filter_by(company_id=company_id).all()
        
        return jsonify({
            'competitors': [comp.to_dict() for comp in competitors]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting competitors: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal Server Error', 'message': 'An error occurred'}), 500


@companies_bp.route('/competitors/<competitor_id>/approve', methods=['POST'])
@requires_authentication
def approve_competitor(competitor_id):
    """Approve competitor for tracking."""
    try:
        success, message = CompetitorDiscoveryService.approve_competitor(competitor_id)
        
        if not success:
            return jsonify({'error': 'Approval Failed', 'message': message}), 400
        
        return jsonify({
            'message': message
        }), 200
        
    except Exception as e:
        logger.error(f"Error approving competitor: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal Server Error', 'message': 'An error occurred'}), 500


@companies_bp.route('/competitors/<competitor_id>/reject', methods=['POST'])
@requires_authentication
def reject_competitor(competitor_id):
    """Reject competitor."""
    try:
        success, message = CompetitorDiscoveryService.reject_competitor(competitor_id)
        
        if not success:
            return jsonify({'error': 'Rejection Failed', 'message': message}), 400
        
        return jsonify({
            'message': message
        }), 200
        
    except Exception as e:
        logger.error(f"Error rejecting competitor: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal Server Error', 'message': 'An error occurred'}), 500
