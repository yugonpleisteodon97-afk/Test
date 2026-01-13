"""
Company and competitor models for Radar application.

Implements Company, Competitor, and TrackingConfig models for
company intake and competitor tracking.
"""

from app.extensions import db
from datetime import datetime, timedelta
import uuid
import enum
import json
from typing import List, Dict, Any, Optional


class ReportFrequency(enum.Enum):
    """Report frequency enumeration."""
    QUARTERLY = 'quarterly'
    MONTHLY = 'monthly'
    ON_DEMAND = 'on-demand'


class Company(db.Model):
    """
    Company model representing the user's company being tracked.
    
    Each user can track one or more companies with their competitors.
    """
    
    __tablename__ = 'companies'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Company information
    name = db.Column(db.String(255), nullable=False)
    website_url = db.Column(db.String(500), nullable=False, index=True)
    industry = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    keywords = db.Column(db.Text, nullable=True)  # JSON array of keywords
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    competitors = db.relationship('Competitor', backref='company', lazy='dynamic', cascade='all, delete-orphan')
    tracking_config = db.relationship('TrackingConfig', backref='company', uselist=False, cascade='all, delete-orphan')
    reports = db.relationship('Report', backref='company', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_keywords(self) -> List[str]:
        """
        Get keywords as Python list.
        
        Returns:
            List of keyword strings
        """
        if not self.keywords:
            return []
        try:
            return json.loads(self.keywords)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_keywords(self, keywords: List[str]):
        """
        Set keywords from Python list.
        
        Args:
            keywords: List of keyword strings
        """
        self.keywords = json.dumps(keywords) if keywords else None
    
    def to_dict(self) -> dict:
        """
        Convert company to dictionary representation.
        
        Returns:
            Company dictionary
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'website_url': self.website_url,
            'industry': self.industry,
            'description': self.description,
            'keywords': self.get_keywords(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Company {self.name}>'


class Competitor(db.Model):
    """
    Competitor model representing a competitor of the tracked company.
    
    Competitors can be discovered automatically or manually added.
    Each competitor is associated with intelligence data and reports.
    """
    
    __tablename__ = 'competitors'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = db.Column(db.String(36), db.ForeignKey('companies.id'), nullable=False, index=True)
    
    # Competitor information
    name = db.Column(db.String(255), nullable=False)
    website_url = db.Column(db.String(500), nullable=False)
    
    # Discovery metadata
    discovery_rationale = db.Column(db.Text, nullable=True)  # Explanation of why this competitor was selected
    confidence_score = db.Column(db.Float, nullable=False, default=0.0)  # 0-100
    discovery_source = db.Column(db.String(100), nullable=True)  # 'crunchbase', 'similarweb', 'manual', etc.
    
    # Approval status
    approved_by_user = db.Column(db.Boolean, default=False, nullable=False)
    approved_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    intelligence_data = db.relationship('IntelligenceData', backref='competitor', lazy='dynamic', cascade='all, delete-orphan')
    startups = db.relationship('Startup', backref='competitor', lazy='dynamic', cascade='all, delete-orphan')
    
    def approve(self):
        """Mark competitor as approved by user."""
        self.approved_by_user = True
        self.approved_at = datetime.utcnow()
        db.session.commit()
    
    def reject(self):
        """Mark competitor as rejected (soft delete)."""
        # For now, we'll use approved flag; can add deleted_at for soft deletes
        self.approved_by_user = False
        db.session.commit()
    
    def to_dict(self) -> dict:
        """
        Convert competitor to dictionary representation.
        
        Returns:
            Competitor dictionary
        """
        return {
            'id': self.id,
            'company_id': self.company_id,
            'name': self.name,
            'website_url': self.website_url,
            'discovery_rationale': self.discovery_rationale,
            'confidence_score': self.confidence_score,
            'discovery_source': self.discovery_source,
            'approved_by_user': self.approved_by_user,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Competitor {self.name}>'


class TrackingConfig(db.Model):
    """
    Tracking configuration model for automated report generation.
    
    Defines report frequency, alert thresholds, and delivery settings
    for a tracked company.
    """
    
    __tablename__ = 'tracking_configs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = db.Column(db.String(36), db.ForeignKey('companies.id'), unique=True, nullable=False, index=True)
    
    # Report settings
    report_frequency = db.Column(db.Enum(ReportFrequency), nullable=False, default=ReportFrequency.QUARTERLY)
    
    # Alert thresholds (JSON)
    alert_thresholds = db.Column(db.Text, nullable=True)  # JSON: M&A, funding, IP spikes
    
    # Email settings
    email_recipients = db.Column(db.Text, nullable=True)  # JSON array of email addresses
    
    # Scheduling
    last_report_generated_at = db.Column(db.DateTime, nullable=True)
    next_report_due_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def get_alert_thresholds(self) -> Dict[str, Any]:
        """
        Get alert thresholds as Python dictionary.
        
        Returns:
            Dictionary of alert thresholds
        """
        if not self.alert_thresholds:
            return {
                'm_a_spike': False,  # Trigger on M&A activity
                'funding_spike': False,  # Trigger on funding rounds
                'ip_spike': False,  # Trigger on patent activity
                'news_sentiment_drop': -0.3,  # Trigger on sentiment drop
                'traffic_growth_spike': 0.2  # Trigger on 20% traffic growth
            }
        try:
            return json.loads(self.alert_thresholds)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_alert_thresholds(self, thresholds: Dict[str, Any]):
        """
        Set alert thresholds from Python dictionary.
        
        Args:
            thresholds: Dictionary of alert thresholds
        """
        self.alert_thresholds = json.dumps(thresholds) if thresholds else None
    
    def get_email_recipients(self) -> List[str]:
        """
        Get email recipients as Python list.
        
        Returns:
            List of email addresses
        """
        if not self.email_recipients:
            return []
        try:
            return json.loads(self.email_recipients)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_email_recipients(self, recipients: List[str]):
        """
        Set email recipients from Python list.
        
        Args:
            recipients: List of email addresses
        """
        self.email_recipients = json.dumps(recipients) if recipients else None
    
    def calculate_next_report_date(self) -> datetime:
        """
        Calculate next report due date based on frequency.
        
        Returns:
            Next report due datetime
        """
        base_date = self.last_report_generated_at or datetime.utcnow()
        
        if self.report_frequency == ReportFrequency.QUARTERLY:
            # Add 3 months
            next_date = base_date + timedelta(days=90)
        elif self.report_frequency == ReportFrequency.MONTHLY:
            # Add 1 month
            next_date = base_date + timedelta(days=30)
        else:  # ON_DEMAND
            next_date = None
        
        return next_date
    
    def update_next_report_date(self):
        """Update next report due date based on current frequency."""
        self.next_report_due_at = self.calculate_next_report_date()
        db.session.commit()
    
    def mark_report_generated(self):
        """Mark report as generated and update next due date."""
        self.last_report_generated_at = datetime.utcnow()
        self.update_next_report_date()
        db.session.commit()
    
    def to_dict(self) -> dict:
        """
        Convert tracking config to dictionary representation.
        
        Returns:
            Tracking config dictionary
        """
        return {
            'id': self.id,
            'company_id': self.company_id,
            'report_frequency': self.report_frequency.value if self.report_frequency else None,
            'alert_thresholds': self.get_alert_thresholds(),
            'email_recipients': self.get_email_recipients(),
            'last_report_generated_at': self.last_report_generated_at.isoformat() if self.last_report_generated_at else None,
            'next_report_due_at': self.next_report_due_at.isoformat() if self.next_report_due_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<TrackingConfig {self.company_id}>'
