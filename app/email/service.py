"""Email delivery service using SendGrid."""

from flask import current_app, render_template
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
from typing import List, Optional, Dict, Any
import base64
import logging
from pathlib import Path


logger = logging.getLogger(__name__)


class EmailService:
    """Email delivery service using SendGrid."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize email service.
        
        Args:
            api_key: SendGrid API key (defaults to config)
        """
        self.api_key = api_key or current_app.config.get('SENDGRID_API_KEY')
        if self.api_key:
            self.client = SendGridAPIClient(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("SendGrid API key not configured")
    
    def send_report_email(
        self,
        to_emails: List[str],
        subject: str,
        report_path: Optional[Path] = None,
        company_name: str = "Your Company"
    ) -> bool:
        """
        Send report delivery email.
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            report_path: Path to PDF report file (optional)
            company_name: Company name for personalization
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            if not self.client:
                logger.error("SendGrid client not initialized")
                return False
            
            # Render email template
            html_content = render_template(
                'email/report_delivery.html',
                company_name=company_name,
                report_attached=report_path is not None
            )
            
            # Create email
            message = Mail(
                from_email=current_app.config.get('SENDGRID_FROM_EMAIL', 'noreply@radar.com'),
                to_emails=to_emails,
                subject=subject,
                html_content=html_content
            )
            
            # Attach report if provided
            if report_path and report_path.exists():
                with open(report_path, 'rb') as f:
                    data = f.read()
                    encoded = base64.b64encode(data).decode()
                    
                    attachment = Attachment(
                        FileContent(encoded),
                        FileName(report_path.name),
                        FileType('application/pdf'),
                        Disposition('attachment')
                    )
                    message.add_attachment(attachment)
            
            # Send email
            response = self.client.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Report email sent successfully to: {', '.join(to_emails)}")
                return True
            else:
                logger.error(f"Failed to send email: {response.status_code} - {response.body}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}", exc_info=True)
            return False
    
    def send_alert_email(
        self,
        to_emails: List[str],
        alert_type: str,
        alert_data: Dict[str, Any],
        company_name: str = "Your Company"
    ) -> bool:
        """
        Send alert email (M&A, funding, IP spikes, etc.).
        
        Args:
            to_emails: List of recipient email addresses
            alert_type: Type of alert ('m_a', 'funding', 'ip_spike', etc.)
            alert_data: Alert data dictionary
            company_name: Company name for personalization
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            if not self.client:
                logger.error("SendGrid client not initialized")
                return False
            
            # Render alert template
            html_content = render_template(
                'email/alert.html',
                company_name=company_name,
                alert_type=alert_type,
                alert_data=alert_data
            )
            
            # Create email
            subject = f"Radar Alert: {alert_type.replace('_', ' ').title()} - {company_name}"
            message = Mail(
                from_email=current_app.config.get('SENDGRID_FROM_EMAIL', 'noreply@radar.com'),
                to_emails=to_emails,
                subject=subject,
                html_content=html_content
            )
            
            # Send email
            response = self.client.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Alert email sent successfully to: {', '.join(to_emails)}")
                return True
            else:
                logger.error(f"Failed to send alert email: {response.status_code} - {response.body}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending alert email: {str(e)}", exc_info=True)
            return False
