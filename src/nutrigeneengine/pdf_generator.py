"""
PDF Report Generator

Generates professional PDF reports with embedded visualizations and trait explanations.
Supports English and Turkish localization.
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Python 3.8 compatibility fix for reportlab
if sys.version_info < (3, 9):
    import hashlib
    _orig_md5 = hashlib.md5
    def _compat_md5(*args, **kwargs):
        kwargs.pop('usedforsecurity', None)
        return _orig_md5(*args, **kwargs)
    hashlib.md5 = _compat_md5

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
    
    # Try to register Unicode-compatible fonts for Turkish characters
    UNICODE_FONT_AVAILABLE = False
    possible_fonts = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        '/System/Library/Fonts/Arial.ttf',
        'C:\\Windows\\Fonts\\arial.ttf',
        'C:\\Windows\\Fonts\\tahoma.ttf'
    ]
    
    possible_bold_fonts = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
        '/System/Library/Fonts/Arial Bold.ttf',
        'C:\\Windows\\Fonts\\arialbd.ttf',
        'C:\\Windows\\Fonts\\tahomabd.ttf'
    ]

    # Attempt to load a font
    font_path = None
    font_bold_path = None
    
    for path in possible_fonts:
        if os.path.exists(path):
            font_path = path
            break
            
    for path in possible_bold_fonts:
        if os.path.exists(path):
            font_bold_path = path
            break

    if font_path and font_bold_path:
        try:
            pdfmetrics.registerFont(TTFont('CustomFont', font_path))
            pdfmetrics.registerFont(TTFont('CustomFont-Bold', font_bold_path))
            UNICODE_FONT_AVAILABLE = True
        except Exception as e:
            pass

except ImportError:
    REPORTLAB_AVAILABLE = False
    UNICODE_FONT_AVAILABLE = False


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
        'variant': 'Variant',
        'references': 'References'
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
        'variant': 'Varyant',
        'references': 'Referanslar'
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
        """Create custom paragraph styles with Unicode font support for Turkish characters."""
        styles = getSampleStyleSheet()
        
        # Select appropriate fonts
        title_font = 'CustomFont' if UNICODE_FONT_AVAILABLE else 'Helvetica'
        title_font_bold = 'CustomFont-Bold' if UNICODE_FONT_AVAILABLE else 'Helvetica-Bold'
        
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName=title_font_bold
        ))
        styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=styles['Heading2'],
            fontSize=18,
            textColor=colors.HexColor('#283593'),
            spaceAfter=12,
            spaceBefore=12,
            fontName=title_font_bold
        ))
        styles.add(ParagraphStyle(
            name='TraitHeader',
            parent=styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=12,
            spaceBefore=12,
            fontName=title_font_bold
        ))
        styles.add(ParagraphStyle(
            name='VariantHeader',
            parent=styles['Heading4'],
            fontSize=12,
            textColor=colors.HexColor('#283593'),
            spaceAfter=8,
            spaceBefore=8,
            fontName=title_font_bold
        ))
        styles.add(ParagraphStyle(
            name='NoteKey',
            parent=styles['Normal'],
            fontSize=10,
            fontName=title_font_bold,
            spaceAfter=4,
            textColor=colors.HexColor('#283593')
        ))
        styles.add(ParagraphStyle(
            name='DetailText',
            parent=styles['BodyText'],
            fontSize=10,
            alignment=TA_JUSTIFY,
            spaceAfter=12,
            leading=14,
            fontName=title_font
        ))
        # Override Normal style to use Unicode font
        styles['Normal'].fontName = title_font
        styles['Normal'].fontSize = 10
        styles['Normal'].spaceAfter = 8
        
        return styles
    
    def _build_trait_cache(self) -> Dict[str, Any]:
        """Build cache of trait info from schema for quick lookup."""
        cache = {}
        for group in self.schema.get('taxonomy', {}).get('top_groups', []):
            for trait in group.get('traits', []):
                cache[trait.get('name')] = trait
        return cache
    
    def _get_all_traits_by_group(self):
        """Get all traits organized by group/domain."""
        groups = {}
        for group in self.schema.get('taxonomy', {}).get('top_groups', []):
            group_name = group.get('name', 'Unknown')
            if group_name not in groups:
                groups[group_name] = []
            for trait in group.get('traits', []):
                groups[group_name].append(trait)
        return groups
    
    def _find_variant_details(self, trait_name):
        """Find variant details for a trait from schema."""
        for group in self.schema.get('taxonomy', {}).get('top_groups', []):
            for trait in group.get('traits', []):
                if trait.get('name') == trait_name:
                    return trait.get('variants', [])
        return []
    
    def generate_report(self, output_path: str, profile_name: Optional[str] = None, image_path: Optional[str] = None):
        """
        Generate comprehensive PDF with detailed variant effects grouped by risk category.
        """
        output_dir = os.path.dirname(output_path) or '.'
        output_base = os.path.basename(output_path).replace('_risk_report.pdf', '').replace('_risk_report_TR.pdf', '')
        
        suffix = '_TR' if self.language == 'tr' else ''
        summary_image = os.path.join(output_dir, f"{output_base}_summary_risk_graph{suffix}.png")
        group_image = os.path.join(output_dir, f"{output_base}_group_risk_graphs{suffix}.png")
        
        doc = SimpleDocTemplate(output_path, pagesize=letter,
                              rightMargin=0.5*inch, leftMargin=0.5*inch,
                              topMargin=0.75*inch, bottomMargin=0.75*inch)
        story = []
        
        # Title page
        story.append(Paragraph(self.ui_text['title'], self.styles['CustomTitle']))
        story.append(Spacer(1, 0.3*inch))
        meta_text = f"<b>{self.ui_text['generated']}</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        story.append(Paragraph(meta_text, self.styles['Normal']))
        story.append(Spacer(1, 0.4*inch))
        
        # Summary image
        if os.path.exists(summary_image):
            story.append(Paragraph(self.ui_text['summary'], self.styles['CustomHeading']))
            story.append(Spacer(1, 0.15*inch))
            try:
                img = Image(summary_image, width=6*inch, height=4.5*inch)
                story.append(img)
            except:
                pass
        
        story.append(PageBreak())
        
        # Get traits organized by group
        groups = self._get_all_traits_by_group()
        sorted_results = sorted(self.results.items(), 
                              key=lambda x: x[1].get('percentage', 0), 
                              reverse=True)
        
        # Group results by category
        results_by_group = {}
        for trait_name, trait_data in sorted_results:
            trait_group = None
            for group_name, traits in groups.items():
                for trait in traits:
                    if trait.get('name') == trait_name:
                        trait_group = group_name
                        break
                if trait_group:
                    break
            if trait_group:
                if trait_group not in results_by_group:
                    results_by_group[trait_group] = []
                results_by_group[trait_group].append((trait_name, trait_data))
        
        # Detailed reports by category
        for group_name in sorted(results_by_group.keys()):
            story.append(Paragraph(f"<b>Risk Category: {group_name}</b>", self.styles['CustomHeading']))
            story.append(Spacer(1, 0.15*inch))
            
            for trait_name, trait_data in results_by_group[group_name]:
                percentage = trait_data.get('percentage', 0)
                classification = trait_data.get('classification', 'UNKNOWN')
                risk_color = '#4CAF50' if percentage <= 33 else '#FFC107' if percentage <= 66 else '#F44336'
                
                header_text = f"<b>{trait_name}</b> - Score: <font color='{risk_color}'><b>{percentage:.1f}% ({classification})</b></font>"
                story.append(Paragraph(header_text, self.styles['TraitHeader']))
                story.append(Spacer(1, 0.1*inch))
                
                # Variant details
                variants = self._find_variant_details(trait_name)
                for idx, variant in enumerate(variants, 1):
                    rsid = variant.get('rsid', f'Variant {idx}')
                    gene_name = variant.get('gene', {}).get('name', 'Unknown') if isinstance(variant.get('gene'), dict) else variant.get('gene', 'Unknown')
                    
                    story.append(Paragraph(f"<b>{self.ui_text['variant']} {idx}: {rsid}</b>", self.styles['VariantHeader']))
                    story.append(Spacer(1, 0.05*inch))
                    story.append(Paragraph(f"<b>{self.ui_text['gene']}: {gene_name}</b>", self.styles['Normal']))
                    story.append(Spacer(1, 0.08*inch))
                    
                    # Effect notes
                    effect = variant.get('effect', {})
                    if 'notes' in effect and isinstance(effect['notes'], dict):
                        for note_key, note_text in effect['notes'].items():
                            section_title = note_key.replace('_', ' ').title()
                            story.append(Paragraph(f"<b>{section_title}:</b>", self.styles['NoteKey']))
                            story.append(Paragraph(note_text, self.styles['DetailText']))
                            story.append(Spacer(1, 0.08*inch))
                    
                    # Studies
                    if 'studies' in effect and effect['studies']:
                        story.append(Paragraph(f"<b>{self.ui_text['references']}:</b>", self.styles['Normal']))
                        story.append(Spacer(1, 0.05*inch))
                        for study in effect['studies']:
                            title = study.get('title', 'N/A')
                            url = study.get('url', '')
                            ref_text = f"• <b>{title}</b><br/><font color='blue'><u>{url}</u></font>" if url else f"• {title}"
                            story.append(Paragraph(ref_text, self.styles['Normal']))
                            story.append(Spacer(1, 0.04*inch))
                        story.append(Spacer(1, 0.1*inch))
                    else:
                        story.append(Spacer(1, 0.1*inch))
                
                story.append(Spacer(1, 0.15*inch))
            
            story.append(PageBreak())
        
        # Group graphs
        if os.path.exists(group_image):
            title = "Kategorilere Göre Detaylı Risk Profilleri" if self.language == 'tr' else "Detailed Risk Profiles by Category"
            story.append(Paragraph(f"<b>{title}</b>", self.styles['CustomHeading']))
            story.append(Spacer(1, 0.2*inch))
            try:
                img = Image(group_image, width=6.5*inch, height=7*inch)
                story.append(img)
            except:
                pass
        
        doc.build(story)
