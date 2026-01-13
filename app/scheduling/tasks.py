"""Celery tasks for scheduled report generation and alerts."""

from app.extensions import celery, db
from app.reports.generator import ReportGenerator
from app.reports.models import Report, ReportType
from app.companies.models import Company, TrackingConfig, ReportFrequency
from app.intelligence.engine import IntelligenceEngine
from app.email.service import EmailService
from app.config import Config
from pathlib import Path
from datetime import datetime, timedelta
import logging


logger = logging.getLogger(__name__)


@celery.task(name='generate_quarterly_report')
def generate_quarterly_report(company_id: str, user_id: str):
    """
    Generate quarterly report for a company.
    
    Celery task that:
    1. Collects intelligence data
    2. Generates PDF report
    3. Sends email notification
    
    Args:
        company_id: Company ID
        user_id: User ID
    """
    try:
        logger.info(f"Starting quarterly report generation for company: {company_id}")
        
        # Get company and tracking config
        company = Company.query.get(company_id)
        if not company:
            logger.error(f"Company not found: {company_id}")
            return False
        
        tracking_config = company.tracking_config
        if not tracking_config:
            logger.error(f"Tracking config not found for company: {company_id}")
            return False
        
        # Collect intelligence data for all approved competitors
        intelligence_engine = IntelligenceEngine()
        competitors = [c for c in company.competitors if c.approved_by_user]
        
        for competitor in competitors:
            competitor_data = {
                'name': competitor.name,
                'website_url': competitor.website_url
            }
            intelligence_engine.run_collection(competitor.id, competitor_data)
        
        # Generate report
        generator = ReportGenerator(Path(Config.REPORT_OUTPUT_DIR))
        period_end = datetime.utcnow()
        period_start = period_end - timedelta(days=90)  # Last quarter
        
        report = generator.generate_report(
            company_id=company_id,
            user_id=user_id,
            report_type=ReportType.QUARTERLY,
            period_start=period_start,
            period_end=period_end
        )
        
        if not report:
            logger.error(f"Failed to generate report for company: {company_id}")
            return False
        
        # Save report
        db.session.add(report)
        db.session.commit()
        
        # Send email notification
        email_service = EmailService()
        recipients = tracking_config.get_email_recipients()
        if recipients:
            subject = f"Quarterly Intelligence Report - {company.name}"
            email_service.send_report_email(
                to_emails=recipients,
                subject=subject,
                report_path=Path(report.pdf_file_path) if report.pdf_file_path else None,
                company_name=company.name
            )
            
            report.mark_delivered()
        
        # Update tracking config
        tracking_config.mark_report_generated()
        
        logger.info(f"Quarterly report generated successfully for company: {company_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error generating quarterly report: {str(e)}", exc_info=True)
        return False


@celery.task(name='check_alerts')
def check_alerts(company_id: str):
    """
    Check for alert conditions and send notifications.
    
    Args:
        company_id: Company ID
    """
    try:
        # TODO: Implement alert checking logic
        # Check for M&A activity, funding spikes, IP activity, etc.
        logger.info(f"Checking alerts for company: {company_id}")
        
        # Placeholder - would check intelligence data for alert conditions
        # and send email notifications if thresholds are exceeded
        
        return True
        
    except Exception as e:
        logger.error(f"Error checking alerts: {str(e)}", exc_info=True)
        return False


@celery.task(name='collect_intelligence')
def collect_intelligence(competitor_id: str):
    """
    Collect intelligence data for a competitor.
    
    Args:
        competitor_id: Competitor ID
    """
    try:
        from app.companies.models import Competitor
        
        competitor = Competitor.query.get(competitor_id)
        if not competitor:
            logger.error(f"Competitor not found: {competitor_id}")
            return False
        
        # Collect intelligence
        intelligence_engine = IntelligenceEngine()
        competitor_data = {
            'name': competitor.name,
            'website_url': competitor.website_url
        }
        
        result = intelligence_engine.run_collection(competitor.id, competitor_data)
        
        logger.info(f"Intelligence collection completed for competitor: {competitor_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error collecting intelligence: {str(e)}", exc_info=True)
        return False
