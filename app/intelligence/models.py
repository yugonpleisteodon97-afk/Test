"""
Intelligence data models for Radar application.

Implements IntelligenceData and Startup models for storing collected
intelligence and analyzed insights.
"""

from app.extensions import db
from datetime import datetime, timedelta
import uuid
import enum
import json
from typing import Dict, Any, List, Optional


class DataType(enum.Enum):
    """Intelligence data type enumeration."""
    FINANCIAL = 'financial'
    PATENTS = 'patents'
    NEWS = 'news'
    TRAFFIC = 'traffic'
    SOCIAL = 'social'
    FUNDING = 'funding'
    M_A = 'm_a'
    HIRING = 'hiring'


class IntelligenceData(db.Model):
    """
    Intelligence data model for storing collected and analyzed intelligence.
    
    Stores raw API responses, processed insights, and metadata for each
    competitor and data type. Supports versioning and cache expiration.
    """
    
    __tablename__ = 'intelligence_data'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    competitor_id = db.Column(db.String(36), db.ForeignKey('competitors.id'), nullable=False, index=True)
    
    # Data classification
    data_type = db.Column(db.Enum(DataType), nullable=False, index=True)
    source = db.Column(db.String(100), nullable=False)  # API name: 'alpha_vantage', 'crunchbase', etc.
    
    # Data storage (JSONB-like using Text with JSON)
    raw_data = db.Column(db.Text, nullable=True)  # Full API response
    analyzed_data = db.Column(db.Text, nullable=True)  # Processed insights
    
    # Quality metrics
    confidence_score = db.Column(db.Float, nullable=False, default=0.0)  # 0-100
    version = db.Column(db.Integer, default=1, nullable=False)  # For data versioning
    
    # Cache management
    collected_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=True, index=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Index for efficient queries
    __table_args__ = (
        db.Index('idx_competitor_data_type', 'competitor_id', 'data_type'),
        db.Index('idx_expires_at', 'expires_at'),
    )
    
    def get_raw_data(self) -> Optional[Dict[str, Any]]:
        """
        Get raw data as Python dictionary.
        
        Returns:
            Dictionary of raw data or None
        """
        if not self.raw_data:
            return None
        try:
            return json.loads(self.raw_data)
        except (json.JSONDecodeError, TypeError):
            return None
    
    def set_raw_data(self, data: Dict[str, Any]):
        """
        Set raw data from Python dictionary.
        
        Args:
            data: Dictionary of raw data
        """
        self.raw_data = json.dumps(data, default=str) if data else None
    
    def get_analyzed_data(self) -> Optional[Dict[str, Any]]:
        """
        Get analyzed data as Python dictionary.
        
        Returns:
            Dictionary of analyzed data or None
        """
        if not self.analyzed_data:
            return None
        try:
            return json.loads(self.analyzed_data)
        except (json.JSONDecodeError, TypeError):
            return None
    
    def set_analyzed_data(self, data: Dict[str, Any]):
        """
        Set analyzed data from Python dictionary.
        
        Args:
            data: Dictionary of analyzed data
        """
        self.analyzed_data = json.dumps(data, default=str) if data else None
    
    def is_expired(self) -> bool:
        """
        Check if data has expired.
        
        Returns:
            True if expired or no expiration set, False otherwise
        """
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def set_expiration(self, ttl_seconds: int):
        """
        Set expiration time based on TTL.
        
        Args:
            ttl_seconds: Time to live in seconds
        """
        self.expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
    
    def increment_version(self):
        """Increment data version for tracking changes."""
        self.version += 1
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self, include_raw: bool = False) -> dict:
        """
        Convert intelligence data to dictionary representation.
        
        Args:
            include_raw: If True, includes raw data
            
        Returns:
            Intelligence data dictionary
        """
        data = {
            'id': self.id,
            'competitor_id': self.competitor_id,
            'data_type': self.data_type.value if self.data_type else None,
            'source': self.source,
            'confidence_score': self.confidence_score,
            'version': self.version,
            'collected_at': self.collected_at.isoformat() if self.collected_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_expired': self.is_expired(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_raw:
            data['raw_data'] = self.get_raw_data()
        
        data['analyzed_data'] = self.get_analyzed_data()
        
        return data
    
    def __repr__(self):
        return f'<IntelligenceData {self.data_type.value} for {self.competitor_id}>'


class Startup(db.Model):
    """
    Startup model for ecosystem-relevant startups.
    
    Represents potential disruptors, partners, or acquisition targets
    discovered through competitive intelligence analysis.
    """
    
    __tablename__ = 'startups'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    competitor_id = db.Column(db.String(36), db.ForeignKey('competitors.id'), nullable=True, index=True)  # Nullable (can be standalone)
    company_id = db.Column(db.String(36), db.ForeignKey('companies.id'), nullable=True, index=True)  # For direct association
    
    # Startup information
    name = db.Column(db.String(255), nullable=False)
    website_url = db.Column(db.String(500), nullable=True)
    description = db.Column(db.Text, nullable=True)
    
    # Funding information
    funding_total = db.Column(db.Numeric(20, 2), nullable=True)  # Total funding amount
    funding_stages = db.Column(db.Text, nullable=True)  # JSON array of funding rounds
    latest_funding_date = db.Column(db.DateTime, nullable=True)
    latest_funding_round = db.Column(db.String(50), nullable=True)  # 'Seed', 'Series A', etc.
    
    # Team information
    key_hires = db.Column(db.Text, nullable=True)  # JSON array of key hires
    employee_count = db.Column(db.Integer, nullable=True)
    
    # Analysis results
    innovation_signals = db.Column(db.Text, nullable=True)  # JSON: patent activity, R&D intensity
    swot_analysis = db.Column(db.Text, nullable=True)  # JSON: strengths, weaknesses, opportunities, threats
    relevance_score = db.Column(db.Float, nullable=False, default=0.0)  # 0-100
    
    # Strategic classification
    strategic_role = db.Column(db.String(50), nullable=True)  # 'disruptor', 'partner', 'acquisition_target'
    
    # Timestamps
    discovered_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def get_funding_stages(self) -> List[Dict[str, Any]]:
        """
        Get funding stages as Python list.
        
        Returns:
            List of funding stage dictionaries
        """
        if not self.funding_stages:
            return []
        try:
            return json.loads(self.funding_stages)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_funding_stages(self, stages: List[Dict[str, Any]]):
        """
        Set funding stages from Python list.
        
        Args:
            stages: List of funding stage dictionaries
        """
        self.funding_stages = json.dumps(stages, default=str) if stages else None
    
    def get_key_hires(self) -> List[Dict[str, Any]]:
        """
        Get key hires as Python list.
        
        Returns:
            List of key hire dictionaries
        """
        if not self.key_hires:
            return []
        try:
            return json.loads(self.key_hires)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_key_hires(self, hires: List[Dict[str, Any]]):
        """
        Set key hires from Python list.
        
        Args:
            hires: List of key hire dictionaries
        """
        self.key_hires = json.dumps(hires, default=str) if hires else None
    
    def get_innovation_signals(self) -> Dict[str, Any]:
        """
        Get innovation signals as Python dictionary.
        
        Returns:
            Dictionary of innovation signals
        """
        if not self.innovation_signals:
            return {}
        try:
            return json.loads(self.innovation_signals)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_innovation_signals(self, signals: Dict[str, Any]):
        """
        Set innovation signals from Python dictionary.
        
        Args:
            signals: Dictionary of innovation signals
        """
        self.innovation_signals = json.dumps(signals, default=str) if signals else None
    
    def get_swot_analysis(self) -> Dict[str, Any]:
        """
        Get SWOT analysis as Python dictionary.
        
        Returns:
            Dictionary with 'strengths', 'weaknesses', 'opportunities', 'threats' keys
        """
        if not self.swot_analysis:
            return {
                'strengths': [],
                'weaknesses': [],
                'opportunities': [],
                'threats': []
            }
        try:
            return json.loads(self.swot_analysis)
        except (json.JSONDecodeError, TypeError):
            return {
                'strengths': [],
                'weaknesses': [],
                'opportunities': [],
                'threats': []
            }
    
    def set_swot_analysis(self, swot: Dict[str, Any]):
        """
        Set SWOT analysis from Python dictionary.
        
        Args:
            swot: Dictionary with SWOT components
        """
        self.swot_analysis = json.dumps(swot, default=str) if swot else None
    
    def to_dict(self) -> dict:
        """
        Convert startup to dictionary representation.
        
        Returns:
            Startup dictionary
        """
        return {
            'id': self.id,
            'competitor_id': self.competitor_id,
            'company_id': self.company_id,
            'name': self.name,
            'website_url': self.website_url,
            'description': self.description,
            'funding_total': float(self.funding_total) if self.funding_total else None,
            'funding_stages': self.get_funding_stages(),
            'latest_funding_date': self.latest_funding_date.isoformat() if self.latest_funding_date else None,
            'latest_funding_round': self.latest_funding_round,
            'key_hires': self.get_key_hires(),
            'employee_count': self.employee_count,
            'innovation_signals': self.get_innovation_signals(),
            'swot_analysis': self.get_swot_analysis(),
            'relevance_score': self.relevance_score,
            'strategic_role': self.strategic_role,
            'discovered_at': self.discovered_at.isoformat() if self.discovered_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Startup {self.name}>'
