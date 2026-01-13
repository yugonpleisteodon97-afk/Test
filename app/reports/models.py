"""
Report models for Radar application.

Implements Report model for storing generated intelligence reports.
"""

from app.extensions import db
from datetime import datetime
import uuid
import enum
import json
from typing import Dict, Any, List, Optional
from decimal import Decimal


class ReportType(enum.Enum):
    """Report type enumeration."""
    QUARTERLY = 'quarterly'
    ON_DEMAND = 'on-demand'
    ALERT = 'alert'


class Report(db.Model):
    """
    Report model for storing generated intelligence reports.
    
    Stores metadata, executive summary, recommendations, and file path
    for generated PDF reports.
    """
    
    __tablename__ = 'reports'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = db.Column(db.String(36), db.ForeignKey('companies.id'), nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Report classification
    report_type = db.Column(db.Enum(ReportType), nullable=False, index=True)
    period_start = db.Column(db.Date, nullable=True)
    period_end = db.Column(db.Date, nullable=True)
    
    # File storage
    pdf_file_path = db.Column(db.String(500), nullable=True)  # Encrypted S3/local path
    file_size = db.Column(db.BigInteger, nullable=True)  # File size in bytes
    checksum = db.Column(db.String(64), nullable=True)  # SHA-256 checksum for integrity
    
    # Executive summary and insights (JSON)
    executive_summary = db.Column(db.Text, nullable=True)  # JSON: key threats, opportunities, recommendations
    threat_scores = db.Column(db.Text, nullable=True)  # JSON: competitor threat scores
    opportunities = db.Column(db.Text, nullable=True)  # JSON array of opportunities
    recommendations = db.Column(db.Text, nullable=True)  # JSON array of recommendations
    
    # Metadata
    overall_confidence = db.Column(db.Float, nullable=True)  # Overall confidence score 0-100
    data_sources = db.Column(db.Text, nullable=True)  # JSON array of data sources used
    methodology_notes = db.Column(db.Text, nullable=True)  # Text notes on methodology
    
    # Delivery status
    generated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    delivery_status = db.Column(db.String(50), nullable=True)  # 'pending', 'sent', 'failed'
    delivery_error = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes for efficient queries
    __table_args__ = (
        db.Index('idx_company_type', 'company_id', 'report_type'),
        db.Index('idx_user_generated', 'user_id', 'generated_at'),
    )
    
    def get_executive_summary(self) -> Optional[Dict[str, Any]]:
        """
        Get executive summary as Python dictionary.
        
        Returns:
            Dictionary with executive summary data
        """
        if not self.executive_summary:
            return None
        try:
            return json.loads(self.executive_summary)
        except (json.JSONDecodeError, TypeError):
            return None
    
    def set_executive_summary(self, summary: Dict[str, Any]):
        """
        Set executive summary from Python dictionary.
        
        Args:
            summary: Dictionary with executive summary data
        """
        self.executive_summary = json.dumps(summary, default=str) if summary else None
    
    def get_threat_scores(self) -> Optional[Dict[str, float]]:
        """
        Get threat scores as Python dictionary.
        
        Returns:
            Dictionary mapping competitor IDs to threat scores (1-10)
        """
        if not self.threat_scores:
            return None
        try:
            return json.loads(self.threat_scores)
        except (json.JSONDecodeError, TypeError):
            return None
    
    def set_threat_scores(self, scores: Dict[str, float]):
        """
        Set threat scores from Python dictionary.
        
        Args:
            scores: Dictionary mapping competitor IDs to threat scores
        """
        self.threat_scores = json.dumps(scores, default=str) if scores else None
    
    def get_opportunities(self) -> List[Dict[str, Any]]:
        """
        Get opportunities as Python list.
        
        Returns:
            List of opportunity dictionaries
        """
        if not self.opportunities:
            return []
        try:
            return json.loads(self.opportunities)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_opportunities(self, opportunities: List[Dict[str, Any]]):
        """
        Set opportunities from Python list.
        
        Args:
            opportunities: List of opportunity dictionaries
        """
        self.opportunities = json.dumps(opportunities, default=str) if opportunities else None
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get recommendations as Python list.
        
        Returns:
            List of recommendation dictionaries
        """
        if not self.recommendations:
            return []
        try:
            return json.loads(self.recommendations)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_recommendations(self, recommendations: List[Dict[str, Any]]):
        """
        Set recommendations from Python list.
        
        Args:
            recommendations: List of recommendation dictionaries
        """
        self.recommendations = json.dumps(recommendations, default=str) if recommendations else None
    
    def get_data_sources(self) -> List[str]:
        """
        Get data sources as Python list.
        
        Returns:
            List of data source strings
        """
        if not self.data_sources:
            return []
        try:
            return json.loads(self.data_sources)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_data_sources(self, sources: List[str]):
        """
        Set data sources from Python list.
        
        Args:
            sources: List of data source strings
        """
        self.data_sources = json.dumps(sources) if sources else None
    
    def mark_delivered(self):
        """Mark report as delivered."""
        self.delivered_at = datetime.utcnow()
        self.delivery_status = 'sent'
        db.session.commit()
    
    def mark_delivery_failed(self, error: str):
        """
        Mark report delivery as failed.
        
        Args:
            error: Error message
        """
        self.delivery_status = 'failed'
        self.delivery_error = error
        db.session.commit()
    
    def to_dict(self, include_full: bool = False) -> dict:
        """
        Convert report to dictionary representation.
        
        Args:
            include_full: If True, includes full data (summary, opportunities, etc.)
            
        Returns:
            Report dictionary
        """
        data = {
            'id': self.id,
            'company_id': self.company_id,
            'user_id': self.user_id,
            'report_type': self.report_type.value if self.report_type else None,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'file_size': self.file_size,
            'checksum': self.checksum,
            'overall_confidence': self.overall_confidence,
            'methodology_notes': self.methodology_notes,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'delivery_status': self.delivery_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_full:
            data['executive_summary'] = self.get_executive_summary()
            data['threat_scores'] = self.get_threat_scores()
            data['opportunities'] = self.get_opportunities()
            data['recommendations'] = self.get_recommendations()
            data['data_sources'] = self.get_data_sources()
            data['pdf_file_path'] = self.pdf_file_path  # Only include if full access
        
        return data
    
    def __repr__(self):
        return f'<Report {self.report_type.value} for {self.company_id}>'
