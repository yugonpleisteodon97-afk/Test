"""Chart generation utilities using Matplotlib and Seaborn."""

from typing import Dict, Any, List, Optional
from pathlib import Path
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import logging


logger = logging.getLogger(__name__)

# Color-blind friendly palette (ColorBrewer)
CB_PALETTE = ['#377eb8', '#ff7f00', '#4daf4a', '#f781bf', '#a65628', '#984ea3', '#999999', '#e41a1c']


class ChartGenerator:
    """Generator for executive report charts."""
    
    def __init__(self, output_dir: Path):
        """
        Initialize chart generator.
        
        Args:
            output_dir: Directory for storing generated charts
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set style
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (10, 6)
        plt.rcParams['font.size'] = 10
    
    def generate_threat_radar_chart(
        self,
        competitor_names: List[str],
        threat_scores: List[float],
        filename: str
    ) -> Optional[Path]:
        """
        Generate threat radar chart for competitors.
        
        Args:
            competitor_names: List of competitor names
            threat_scores: List of threat scores (1-10)
            filename: Output filename
            
        Returns:
            Path to generated chart or None if failed
        """
        try:
            fig, ax = plt.subplots(figsize=(10, 6), subplot_kw=dict(projection='polar'))
            
            # Create chart
            categories = ['Market Overlap', 'Growth Rate', 'Financial Strength', 'Innovation']
            angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
            angles += angles[:1]  # Complete the circle
            
            for i, (name, score) in enumerate(zip(competitor_names, threat_scores)):
                values = [score * 0.3, score * 0.2, score * 0.2, score * 0.3]  # Normalize to categories
                values += values[:1]
                
                ax.plot(angles, values, 'o-', linewidth=2, label=name, color=CB_PALETTE[i % len(CB_PALETTE)])
                ax.fill(angles, values, alpha=0.15, color=CB_PALETTE[i % len(CB_PALETTE)])
            
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(categories)
            ax.set_ylim(0, 10)
            ax.set_title('Competitor Threat Analysis', size=14, fontweight='bold', pad=20)
            ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
            ax.grid(True)
            
            # Save chart
            chart_path = self.output_dir / filename
            plt.tight_layout()
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Threat radar chart generated: {chart_path}")
            return chart_path
            
        except Exception as e:
            logger.error(f"Error generating threat radar chart: {str(e)}", exc_info=True)
            plt.close()
            return None
    
    def generate_financial_trend_chart(
        self,
        companies: List[str],
        data: Dict[str, List[float]],
        filename: str,
        title: str = 'Financial Trend'
    ) -> Optional[Path]:
        """
        Generate financial trend line chart.
        
        Args:
            companies: List of company names
            data: Dictionary mapping company names to data series
            filename: Output filename
            title: Chart title
            
        Returns:
            Path to generated chart or None if failed
        """
        try:
            fig, ax = plt.subplots(figsize=(12, 6))
            
            for i, company in enumerate(companies):
                if company in data:
                    ax.plot(data[company], marker='o', linewidth=2, label=company, color=CB_PALETTE[i % len(CB_PALETTE)])
            
            ax.set_xlabel('Period', fontsize=12)
            ax.set_ylabel('Value', fontsize=12)
            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.legend(loc='best')
            ax.grid(True, alpha=0.3)
            
            # Save chart
            chart_path = self.output_dir / filename
            plt.tight_layout()
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Financial trend chart generated: {chart_path}")
            return chart_path
            
        except Exception as e:
            logger.error(f"Error generating financial trend chart: {str(e)}", exc_info=True)
            plt.close()
            return None
    
    def generate_bar_chart(
        self,
        categories: List[str],
        values: List[float],
        filename: str,
        title: str = 'Bar Chart',
        xlabel: str = 'Category',
        ylabel: str = 'Value'
    ) -> Optional[Path]:
        """
        Generate bar chart.
        
        Args:
            categories: List of category names
            values: List of values
            filename: Output filename
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            
        Returns:
            Path to generated chart or None if failed
        """
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            bars = ax.bar(categories, values, color=CB_PALETTE[:len(categories)])
            ax.set_xlabel(xlabel, fontsize=12)
            ax.set_ylabel(ylabel, fontsize=12)
            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='y')
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.1f}', ha='center', va='bottom')
            
            # Save chart
            chart_path = self.output_dir / filename
            plt.tight_layout()
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Bar chart generated: {chart_path}")
            return chart_path
            
        except Exception as e:
            logger.error(f"Error generating bar chart: {str(e)}", exc_info=True)
            plt.close()
            return None
