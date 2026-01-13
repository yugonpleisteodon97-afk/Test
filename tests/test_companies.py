"""Tests for companies module."""

import pytest
from app.companies.models import Company, Competitor
from app.companies.services import CompanyService, CompetitorDiscoveryService
from app.extensions import db


class TestCompanyService:
    """Test company service."""
    
    def test_create_company(self, app, test_user):
        """Test company creation."""
        with app.app_context():
            company, success, message = CompanyService.create_company(
                user_id=test_user.id,
                website_url='https://example.com',
                name='Example Company'
            )
            
            assert success is True
            assert company is not None
            assert company.name == 'Example Company'
            assert company.website_url == 'https://example.com'


class TestCompetitorDiscovery:
    """Test competitor discovery."""
    
    def test_create_competitor(self, app, test_company):
        """Test competitor creation."""
        with app.app_context():
            competitor, success, message = CompetitorDiscoveryService.create_competitor(
                company_id=test_company.id,
                name='Competitor Company',
                website_url='https://competitor.com',
                confidence_score=85.0,
                discovery_source='manual'
            )
            
            assert success is True
            assert competitor is not None
            assert competitor.name == 'Competitor Company'
            assert competitor.confidence_score == 85.0
