"""
Intelligence orchestrator for Radar application.

Coordinates all collectors, executes in parallel, aggregates data,
and calculates confidence scores.
"""

from app.intelligence.collectors.financial import FinancialCollector
from app.intelligence.collectors.funding import FundingCollector
from app.intelligence.collectors.patents import PatentsCollector
from app.intelligence.collectors.news import NewsCollector
from app.intelligence.collectors.traffic import TrafficCollector
from app.intelligence.collectors.social import SocialCollector
from app.intelligence.models import IntelligenceData, DataType
from app.extensions import db
from typing import Dict, Any, List, Optional, Tuple
import asyncio
import logging
from datetime import datetime


logger = logging.getLogger(__name__)


class IntelligenceEngine:
    """Main intelligence orchestrator."""
    
    def __init__(self):
        """Initialize intelligence engine with all collectors."""
        self.collectors = {
            'financial': FinancialCollector(),
            'funding': FundingCollector(),
            'patents': PatentsCollector(),
            'news': NewsCollector(),
            'traffic': TrafficCollector(),
            'social': SocialCollector()
        }
    
    async def collect_all_async(self, competitor_id: str, competitor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Collect all intelligence data asynchronously.
        
        Args:
            competitor_id: Competitor ID
            competitor_data: Competitor metadata
            
        Returns:
            Dictionary mapping data types to collected data
        """
        # Create tasks for all collectors
        tasks = []
        for data_type, collector in self.collectors.items():
            task = asyncio.create_task(
                self._collect_single(collector, competitor_id, competitor_data, data_type)
            )
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        collected_data = {}
        for i, (data_type, result) in enumerate(zip(self.collectors.keys(), results)):
            if isinstance(result, Exception):
                logger.error(f"Error collecting {data_type}: {str(result)}", exc_info=True)
                collected_data[data_type] = {
                    'data': None,
                    'confidence_score': 0,
                    'error': str(result)
                }
            else:
                data, confidence, error = result
                collected_data[data_type] = {
                    'data': data,
                    'confidence_score': confidence,
                    'error': error
                }
        
        return collected_data
    
    async def _collect_single(
        self,
        collector: Any,
        competitor_id: str,
        competitor_data: Dict[str, Any],
        data_type: str
    ) -> Tuple[Optional[Dict[str, Any]], float, str]:
        """Collect data from a single collector (async wrapper)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            collector.collect,
            competitor_id,
            competitor_data
        )
    
    def collect_all(self, competitor_id: str, competitor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Collect all intelligence data (synchronous wrapper).
        
        Args:
            competitor_id: Competitor ID
            competitor_data: Competitor metadata
            
        Returns:
            Dictionary mapping data types to collected data
        """
        try:
            # Run async collection
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(self.collect_all_async(competitor_id, competitor_data))
            loop.close()
            
            return results
            
        except Exception as e:
            logger.error(f"Error in intelligence collection: {str(e)}", exc_info=True)
            return {}
    
    def store_intelligence_data(
        self,
        competitor_id: str,
        collected_data: Dict[str, Any]
    ) -> List[IntelligenceData]:
        """
        Store collected intelligence data in database.
        
        Args:
            competitor_id: Competitor ID
            collected_data: Collected data dictionary
            
        Returns:
            List of IntelligenceData objects
        """
        stored_records = []
        
        for data_type_str, data_info in collected_data.items():
            try:
                # Map string to enum
                data_type_map = {
                    'financial': DataType.FINANCIAL,
                    'funding': DataType.FUNDING,
                    'patents': DataType.PATENTS,
                    'news': DataType.NEWS,
                    'traffic': DataType.TRAFFIC,
                    'social': DataType.SOCIAL
                }
                
                data_type = data_type_map.get(data_type_str)
                if not data_type:
                    continue
                
                # Create or update intelligence data record
                existing = IntelligenceData.query.filter_by(
                    competitor_id=competitor_id,
                    data_type=data_type
                ).first()
                
                if existing:
                    # Update existing record
                    existing.set_raw_data(data_info.get('data', {}))
                    existing.confidence_score = data_info.get('confidence_score', 0)
                    # Get collector for TTL
                collector_instance = self.collectors.get(data_type_str)
                ttl = collector_instance.cache_ttl if collector_instance else 3600
                existing.set_expiration(ttl)  # Set expiration based on collector TTL
                    existing.increment_version()
                    record = existing
                else:
                    # Create new record
                    record = IntelligenceData(
                        competitor_id=competitor_id,
                        data_type=data_type,
                        source=data_type_str,
                        confidence_score=data_info.get('confidence_score', 0)
                    )
                    record.set_raw_data(data_info.get('data', {}))
                    record.set_expiration(
                        self.collectors.get(data_type_str, FinancialCollector()).cache_ttl
                    )
                    db.session.add(record)
                
                stored_records.append(record)
                
            except Exception as e:
                logger.error(f"Error storing {data_type_str} data: {str(e)}", exc_info=True)
                continue
        
        db.session.commit()
        return stored_records
    
    def run_collection(self, competitor_id: str, competitor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run complete intelligence collection workflow.
        
        Args:
            competitor_id: Competitor ID
            competitor_data: Competitor metadata
            
        Returns:
            Dictionary with collection results and metadata
        """
        logger.info(f"Starting intelligence collection for competitor: {competitor_id}")
        
        # Collect all data
        collected_data = self.collect_all(competitor_id, competitor_data)
        
        # Store in database
        stored_records = self.store_intelligence_data(competitor_id, collected_data)
        
        # Calculate overall confidence
        confidence_scores = [
            data_info.get('confidence_score', 0)
            for data_info in collected_data.values()
            if data_info.get('data') is not None
        ]
        
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        logger.info(f"Intelligence collection completed for competitor: {competitor_id}")
        
        return {
            'competitor_id': competitor_id,
            'collected_data': collected_data,
            'stored_records': len(stored_records),
            'overall_confidence': overall_confidence,
            'collected_at': datetime.utcnow().isoformat()
        }
