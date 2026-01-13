"""
Company and competitor services for Radar application.

Implements business logic for company intake, competitor discovery,
and competitor management.
"""

from app.extensions import db
from app.companies.models import Company, Competitor, TrackingConfig, ReportFrequency
from app.auth.models import User
from app.utils.validators import validate_url, ValidationError
from app.utils.security import sanitize_input
from typing import List, Dict, Any, Tuple, Optional
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re


logger = logging.getLogger(__name__)


class CompanyService:
    """Service for company operations."""
    
    @staticmethod
    def create_company(
        user_id: str,
        website_url: str,
        name: Optional[str] = None
    ) -> Tuple[Optional[Company], bool, str]:
        """
        Create company from website URL.
        
        Automatically extracts company information from website.
        
        Args:
            user_id: User ID
            website_url: Company website URL
            name: Company name (optional, will be extracted if not provided)
            
        Returns:
            Tuple of (company, success, message)
        """
        try:
            # Validate URL
            website_url = validate_url(website_url, require_https=False)
            
            # Extract company information
            company_info = CompanyService._extract_company_info(website_url)
            
            # Use provided name or extracted name
            company_name = name or company_info.get('name', 'Unknown Company')
            
            # Check if company already exists for user
            existing = Company.query.filter_by(user_id=user_id, website_url=website_url).first()
            if existing:
                return existing, True, "Company already exists"
            
            # Create company
            company = Company(
                user_id=user_id,
                name=sanitize_input(company_name),
                website_url=website_url,
                industry=company_info.get('industry'),
                description=company_info.get('description'),
                keywords=company_info.get('keywords', [])
            )
            
            db.session.add(company)
            db.session.commit()
            
            # Create default tracking config
            tracking_config = TrackingConfig(
                company_id=company.id,
                report_frequency=ReportFrequency.QUARTERLY
            )
            tracking_config.update_next_report_date()
            db.session.add(tracking_config)
            db.session.commit()
            
            logger.info(f"Company created: {company_name} for user {user_id}")
            
            return company, True, "Company created successfully"
            
        except ValidationError as e:
            return None, False, str(e)
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating company: {str(e)}", exc_info=True)
            return None, False, f"Error creating company: {str(e)}"
    
    @staticmethod
    def _extract_company_info(website_url: str) -> Dict[str, Any]:
        """
        Extract company information from website.
        
        Scrapes website for metadata, description, and keywords.
        
        Args:
            website_url: Company website URL
            
        Returns:
            Dictionary with company information
        """
        try:
            # Fetch webpage
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(website_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract name from title or h1
            name = None
            title_tag = soup.find('title')
            if title_tag:
                name = title_tag.get_text().strip().split('|')[0].strip()
            
            if not name:
                h1_tag = soup.find('h1')
                if h1_tag:
                    name = h1_tag.get_text().strip()
            
            # Extract description from meta description
            description = None
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                description = meta_desc.get('content', '').strip()
            
            # Extract keywords from meta keywords
            keywords = []
            meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
            if meta_keywords:
                keywords = [k.strip() for k in meta_keywords.get('content', '').split(',')]
            
            # Extract industry (basic heuristic)
            industry = None
            # Could be enhanced with industry classification APIs
            
            return {
                'name': name,
                'description': description,
                'keywords': keywords[:10],  # Limit to top 10
                'industry': industry
            }
            
        except Exception as e:
            logger.warning(f"Error extracting company info: {str(e)}")
            return {
                'name': None,
                'description': None,
                'keywords': [],
                'industry': None
            }


class CompetitorDiscoveryService:
    """Service for competitor discovery."""
    
    @staticmethod
    def discover_competitors(
        company: Company,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Discover competitors for a company.
        
        Uses multiple data sources (Crunchbase, SimilarWeb, etc.) to
        identify and score potential competitors.
        
        Args:
            company: Company object
            max_results: Maximum number of competitors to return (default: 5)
            
        Returns:
            List of competitor dictionaries with discovery metadata
        """
        # This is a placeholder implementation
        # In production, this would integrate with:
        # - Crunchbase API for industry-based competitor search
        # - SimilarWeb API for traffic-based competitor suggestions
        # - Patent databases for technology overlap
        # - Cross-reference multiple sources for confidence scoring
        
        competitors = []
        
        # TODO: Implement actual competitor discovery logic
        # For now, return empty list (will be implemented with API integrations)
        
        logger.info(f"Competitor discovery initiated for company: {company.name}")
        
        return competitors[:max_results]
    
    @staticmethod
    def _score_competitor(
        candidate: Dict[str, Any],
        company: Company
    ) -> Dict[str, Any]:
        """
        Score a potential competitor based on multiple factors.
        
        Scoring algorithm:
        - Industry overlap (0-30 points)
        - Geographic proximity (0-20 points)
        - Funding stage similarity (0-25 points)
        - Technology overlap (0-25 points)
        
        Args:
            candidate: Candidate competitor data
            company: Company object for comparison
            
        Returns:
            Dictionary with scored competitor data including confidence score
        """
        # TODO: Implement scoring algorithm
        score = 0
        rationale_parts = []
        
        # Placeholder scoring logic
        # In production, this would analyze:
        # - Industry classification overlap
        # - Geographic proximity (headquarters location)
        # - Funding stage and amount similarity
        # - Patent portfolio overlap
        # - Technology stack similarity
        
        return {
            'name': candidate.get('name'),
            'website_url': candidate.get('website_url'),
            'confidence_score': score,
            'discovery_rationale': ' '.join(rationale_parts) if rationale_parts else 'Potential competitor based on industry analysis',
            'discovery_source': 'crunchbase'  # or 'similarweb', 'patents', etc.
        }
    
    @staticmethod
    def create_competitor(
        company_id: str,
        name: str,
        website_url: str,
        discovery_rationale: str = None,
        confidence_score: float = 0.0,
        discovery_source: str = 'manual'
    ) -> Tuple[Optional[Competitor], bool, str]:
        """
        Create competitor for a company.
        
        Args:
            company_id: Company ID
            name: Competitor name
            website_url: Competitor website URL
            discovery_rationale: Explanation of why this competitor was selected
            confidence_score: Confidence score (0-100)
            discovery_source: Source of discovery
            
        Returns:
            Tuple of (competitor, success, message)
        """
        try:
            website_url = validate_url(website_url, require_https=False)
            
            # Check if competitor already exists
            existing = Competitor.query.filter_by(
                company_id=company_id,
                website_url=website_url
            ).first()
            
            if existing:
                return existing, True, "Competitor already exists"
            
            # Create competitor
            competitor = Competitor(
                company_id=company_id,
                name=sanitize_input(name),
                website_url=website_url,
                discovery_rationale=discovery_rationale,
                confidence_score=confidence_score,
                discovery_source=discovery_source
            )
            
            db.session.add(competitor)
            db.session.commit()
            
            logger.info(f"Competitor created: {name} for company {company_id}")
            
            return competitor, True, "Competitor created successfully"
            
        except ValidationError as e:
            return None, False, str(e)
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating competitor: {str(e)}", exc_info=True)
            return None, False, f"Error creating competitor: {str(e)}"
    
    @staticmethod
    def approve_competitor(competitor_id: str) -> Tuple[bool, str]:
        """
        Approve competitor for tracking.
        
        Args:
            competitor_id: Competitor ID
            
        Returns:
            Tuple of (success, message)
        """
        try:
            competitor = Competitor.query.get(competitor_id)
            if not competitor:
                return False, "Competitor not found"
            
            competitor.approve()
            
            logger.info(f"Competitor approved: {competitor.name}")
            
            return True, "Competitor approved successfully"
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error approving competitor: {str(e)}", exc_info=True)
            return False, f"Error approving competitor: {str(e)}"
    
    @staticmethod
    def reject_competitor(competitor_id: str) -> Tuple[bool, str]:
        """
        Reject competitor (soft delete).
        
        Args:
            competitor_id: Competitor ID
            
        Returns:
            Tuple of (success, message)
        """
        try:
            competitor = Competitor.query.get(competitor_id)
            if not competitor:
                return False, "Competitor not found"
            
            competitor.reject()
            
            logger.info(f"Competitor rejected: {competitor.name}")
            
            return True, "Competitor rejected successfully"
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error rejecting competitor: {str(e)}", exc_info=True)
            return False, f"Error rejecting competitor: {str(e)}"
