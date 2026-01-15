"""
PDF Report Generator

Generates professional PDF reports with embedded visualizations and trait explanations.
Supports English and Turkish localization.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


UI_TEXT = {
    'en': {
        'title': 'Genetic Risk Assessment Report',
        'generated': 'Generated:',
        'profile': 'Profile:',
        'summary': 'Overall Risk Summary',
        'details': 'Detailed Risk Assessment',
        'risk_level': 'Risk Level',
        'score': 'Score',
        'gene': 'Gene',
        'status': 'Status',
        'variant': 'Variant'
    },
    'tr': {
        'title': 'Genetik Risk Değerlendirme Raporu',
        'generated': 'Oluşturulma Tarihi:',
        'profile': 'Profil:',
        'summary': 'Genel Risk Özeti',
        'details': 'Detaylı Risk Değerlendirmesi',
        'risk_level': 'Risk Seviyesi',
        'score': 'Puan',
        'gene': 'Gen',
        'status': 'Durum',
        'variant': 'Varyant'
    }
}


class PDFReportGenerator:
    """
    Generates professional PDF reports for risk assessment results.
    Includes detailed trait explanations, variant information, and references from schema.
    """
    
    def __init__(self, results: Dict[str, Any], schema: Dict[str, Any], language: str = 'en'):
        """
        Initialize the PDF generator.
        
        Args:
            results: Risk assessment results from RiskScorer
            schema: Schema dictionary
            language: 'en' for English or 'tr' for Turkish
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab is required for PDF generation. Install with: pip install reportlab")
        
        self.results = results
        self.schema = schema
        self.language = language
        self.ui_text = UI_TEXT.get(language, UI_TEXT['en'])
        self.styles = self._create_styles()
        self._trait_cache = self._build_trait_cache()
    
    def _create_styles(self):
        """Create custom paragraph styles."""
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2e5c8a'),
            spaceAfter=12,
            spaceBefore=12
        ))
        styles.add(ParagraphStyle(
            name='TraitHeader',
            parent=styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=8,
            spaceBefore=8
        ))
        styles.add(ParagraphStyle(
            name='VariantHeader',
            parent=styles['Heading4'],
            fontSize=11,
            textColor=colors.HexColor('#2e5c8a'),
            spaceAfter=6,
            spaceBefore=6
        ))
        styles.add(ParagraphStyle(
            name='DetailText',
            parent=styles['BodyText'],
            fontSize=10,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
            leading=12
        ))
        return styles
    
    def _build_trait_cache(self) -> Dict[str, Any]:
        """Build cache of trait info from schema for quick lookup."""
        cache = {}
        for group in self.schema.get('taxonomy', {}).get('top_groups', []):
            for trait in group.get('traits', []):
                cache[trait.get('name')] = trait
        return cache
    
    def _get_trait_info(self, trait_name: str) -> Optional[Dict[str, Any]]:
        """Get trait information from cache."""
        return self._trait_cache.get(trait_name)
    
    def generate_report(self, output_path: str, profile_name: Optional[str] = None, image_path: Optional[str] = None):
        """
        Generate a comprehensive PDF report with detailed trait explanations.
        
        Args:
            output_path: Path where to save the PDF
            profile_name: Optional profile/user name
            image_path: Optional path to summary graph image
        """
        doc = SimpleDocTemplate(output_path, pagesize=letter,
                              rightMargin=0.5*inch, leftMargin=0.5*inch,
                              topMargin=0.75*inch, bottomMargin=0.75*inch)
        story = []
        
        # Title
        story.append(Paragraph(self.ui_text['title'], self.styles['CustomTitle']))
        story.append(Spacer(1, 0.2*inch))
        
        # Metadata
        meta_text = f"<b>{self.ui_text['generated']}</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        if profile_name:
            meta_text += f" | <b>Profile:</b> {profile_name}"
        story.append(Paragraph(meta_text, self.styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Summary section with image
        if image_path and os.path.exists(image_path):
            story.append(Paragraph(self.ui_text['summary'], self.styles['CustomHeading']))
            story.append(Image(image_path, width=6*inch, height=4*inch))
            story.append(Spacer(1, 0.2*inch))
        
        story.append(PageBreak())
        
        # Detailed trait reports
        story.append(Paragraph(self.ui_text['details'], self.styles['CustomHeading']))
        story.append(Spacer(1, 0.15*inch))
        
        # Sort by risk (descending)
        sorted_results = sorted(self.results.items(), 
                              key=lambda x: x[1].get('percentage', 0), 
                              reverse=True)
        
        for trait_name, trait_data in sorted_results:
            percentage = trait_data.get('percentage', 0)
            classification = trait_data.get('classification', 'UNKNOWN')
            
            # Color code by risk
            risk_color = '#4CAF50' if percentage <= 33 else '#FFC107' if percentage <= 66 else '#F44336'
            
            # Trait header with score
            header_text = f"<b>{trait_name}</b> - <font color='{risk_color}'><b>{percentage:.1f}% ({classification})</b></font>"
            story.append(Paragraph(header_text, self.styles['TraitHeader']))
            story.append(Spacer(1, 0.08*inch))
            
            # Get trait info from schema
            trait_info = self._get_trait_info(trait_name)
            if trait_info:
                # Description
                if 'description' in trait_info:
                    story.append(Paragraph(f"<i>{trait_info['description']}</i>", self.styles['DetailText']))
                    story.append(Spacer(1, 0.08*inch))
                
                # Variants
                if 'variants' in trait_info:
                    for idx, variant in enumerate(trait_info['variants'], 1):
                        rsid = variant.get('name', variant.get('rsid', f'Variant {idx}'))
                        variant_title = f"<b>{self.ui_text['variant']} {idx}: {rsid}</b>"
                        story.append(Paragraph(variant_title, self.styles['VariantHeader']))
                        
                        # Gene
                        if 'gene' in variant:
                            gene_name = variant['gene'] if isinstance(variant['gene'], str) else variant['gene'].get('name', 'N/A')
                            story.append(Paragraph(f"<b>{self.ui_text['gene']}:</b> {gene_name}", self.styles['Normal']))
                        
                        # Scoring
                        if 'scoring' in variant and 'genotype_points' in variant['scoring']:
                            points = variant['scoring']['genotype_points']
                            pts_text = f"Points: wt={points.get('wt', 0)}, het={points.get('het', 0)}, hom={points.get('hom', 0)}"
                            story.append(Paragraph(pts_text, self.styles['Normal']))
                        
                        story.append(Spacer(1, 0.05*inch))
            
            # Calculation details
            if 'details' in trait_data and trait_data['details']:
                story.append(Paragraph("<b>Calculation Details:</b>", self.styles['Normal']))
                for detail in trait_data['details'][:3]:
                    story.append(Paragraph(f"• {detail}", self.styles['Normal']))
            
            story.append(Spacer(1, 0.15*inch))
        
        # Build
        doc.build(story)
