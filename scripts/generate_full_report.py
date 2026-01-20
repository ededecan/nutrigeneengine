#!/usr/bin/env python
"""
NutriGeneEngine - Full Report Generation
Reads from inputs/ folder, outputs to outputs/ folder
Generates: _risk_report.pdf, _risk_report_TR.pdf, _risk_results.json, 
          _summary_risk_graph.png, _summary_risk_graph_TR.png,
          _group_risk_graphs.png, _group_risk_graphs_TR.png
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Python 3.8 compatibility fix for reportlab
if sys.version_info < (3, 9):
    import hashlib
    _orig_md5 = hashlib.md5
    def _compat_md5(*args, **kwargs):
        kwargs.pop('usedforsecurity', None)
        return _orig_md5(*args, **kwargs)
    hashlib.md5 = _compat_md5

# Get the directory of this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Configuration
SCHEMA_FILENAME = os.path.join(PROJECT_ROOT, 'src/nutrigeneengine/schema.json')
SCHEMA_TR_FILENAME = os.path.join(PROJECT_ROOT, 'src/nutrigeneengine/schema_tr.json')
INPUT_DIR = os.path.join(PROJECT_ROOT, 'inputs')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'outputs')

# Add src to path for imports
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

# Import NutriGeneEngine classes
from nutrigeneengine import RiskScorer, Visualizer, PDFReportGenerator


def create_comprehensive_json(results, schema, language='en'):
    """
    Create comprehensive JSON with all details from the PDF report.
    
    Args:
        results: Risk scores dictionary
        schema: Schema data
        language: 'en' or 'tr'
    
    Returns:
        Dictionary with comprehensive report data
    """
    # Filter out informational traits
    filtered_results = {k: v for k, v in results.items() 
                       if k not in ['Informational', 'Bilgilendirici']}
    
    # Organize by group
    groups_data = {}
    for trait_name, result in filtered_results.items():
        group_name = result.get('group_name', 'Unknown')
        if group_name not in groups_data:
            groups_data[group_name] = []
        groups_data[group_name].append((trait_name, result))
    
    # Build comprehensive report
    report = {
        'metadata': {
            'generated': datetime.now().isoformat(),
            'language': language,
            'title': 'Genetic Risk Assessment Report' if language == 'en' else 'Genetik Risk Değerlendirme Raporu'
        },
        'summary': {
            'total_traits': len(filtered_results),
            'low_risk_count': sum(1 for r in filtered_results.values() if r.get('percentage', 0) <= 33),
            'medium_risk_count': sum(1 for r in filtered_results.values() if 33 < r.get('percentage', 0) <= 66),
            'high_risk_count': sum(1 for r in filtered_results.values() if r.get('percentage', 0) > 66),
        },
        'risk_categories': {}
    }
    
    # Add detailed trait information organized by category
    for group_name in sorted(groups_data.keys()):
        traits = sorted(groups_data[group_name], key=lambda x: x[1].get('percentage', 0), reverse=True)
        
        category_data = {
            'traits': []
        }
        
        for trait_name, trait_result in traits:
            trait_info = {
                'name': trait_name,
                'percentage': trait_result.get('percentage', 0),
                'classification': trait_result.get('classification', 'UNKNOWN'),
                'group_name': trait_result.get('group_name', 'Unknown'),
                'variants': []
            }
            
            # Find variant details from schema
            if schema and 'taxonomy' in schema:
                for group in schema.get('taxonomy', {}).get('top_groups', []):
                    for trait in group.get('traits', []):
                        if trait.get('name') == trait_name:
                            for variant in trait.get('variants', []):
                                variant_info = {
                                    'rsid': variant.get('rsid', 'N/A'),
                                    'gene': variant.get('gene', {}).get('name', 'Unknown') if isinstance(variant.get('gene'), dict) else variant.get('gene', 'Unknown'),
                                    'effect_notes': variant.get('effect', {}).get('notes', {}),
                                    'references': []
                                }
                                
                                # Add references/studies
                                studies = variant.get('effect', {}).get('studies', [])
                                for study in studies:
                                    variant_info['references'].append({
                                        'title': study.get('title', 'N/A'),
                                        'url': study.get('url', '')
                                    })
                                
                                trait_info['variants'].append(variant_info)
            
            category_data['traits'].append(trait_info)
        
        report['risk_categories'][group_name] = category_data
    
    return report



def generate_reports_for_file(input_file):
    """Generate all reports for a given input file"""
    
    try:
        # Load schema
        risk_scorer = RiskScorer.from_file(SCHEMA_FILENAME, language='en')
    except Exception as e:
        return False
    
    # Load Turkish schema
    risk_scorer_tr = None
    if Path(SCHEMA_TR_FILENAME).exists():
        try:
            risk_scorer_tr = RiskScorer.from_file(SCHEMA_TR_FILENAME, language='tr')
        except:
            risk_scorer_tr = None
    
    # Load genotypes from input file
    try:
        with open(input_file, 'r') as f:
            user_data = json.load(f)
        user_genome = user_data['genotypes']
    except (FileNotFoundError, KeyError) as e:
        return False
    
    # Get just the filename (without path)
    filename_base = Path(input_file).stem
    
    try:
        # === ENGLISH REPORTS ===
        
        # Calculate scores
        results = risk_scorer.calculate_score(user_genome)
        
        # Save comprehensive results as JSON with all details
        comprehensive_json = create_comprehensive_json(results, risk_scorer.schema, language='en')
        json_output_path = os.path.join(OUTPUT_DIR, f"{filename_base}_risk_results.json")
        with open(json_output_path, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_json, f, indent=2, ensure_ascii=False)
        
        # Generate visualizations (English)
        visualizer = Visualizer(results, risk_scorer.schema, language='en')
        
        # Generate summary graph
        try:
            summary_path = os.path.join(OUTPUT_DIR, f"{filename_base}_summary_risk_graph.png")
            visualizer.plot_summary_dashboard(summary_path)
        except:
            pass
        
        # Generate domain/group charts
        try:
            visualizer.plot_domain_charts(OUTPUT_DIR, filename_base)
        except:
            pass
        
        # Generate PDF report
        try:
            pdf_generator = PDFReportGenerator(results, risk_scorer.schema, language='en')
            pdf_output_path = os.path.join(OUTPUT_DIR, f"{filename_base}_risk_report.pdf")
            pdf_generator.generate_report(pdf_output_path, profile_name=filename_base)
        except Exception as e:
            pass
        
        # === TURKISH REPORTS ===
        if risk_scorer_tr:
            results_tr = risk_scorer_tr.calculate_score(user_genome)
            visualizer_tr = Visualizer(results_tr, risk_scorer_tr.schema, language='tr')
            
            # Generate summary graph (Turkish)
            try:
                summary_path_tr = os.path.join(OUTPUT_DIR, f"{filename_base}_summary_risk_graph_TR.png")
                visualizer_tr.plot_summary_dashboard(summary_path_tr)
            except:
                pass
            
            # Generate domain/group charts (Turkish)
            try:
                visualizer_tr.plot_domain_charts(OUTPUT_DIR, filename_base, suffix='_TR')
            except:
                pass
            
            # Generate PDF report (Turkish)
            try:
                pdf_generator_tr = PDFReportGenerator(results_tr, risk_scorer_tr.schema, language='tr')
                pdf_output_path_tr = os.path.join(OUTPUT_DIR, f"{filename_base}_risk_report_TR.pdf")
                pdf_generator_tr.generate_report(pdf_output_path_tr, profile_name=filename_base)
            except Exception as e:
                pass
            
            # Save comprehensive JSON report (Turkish)
            try:
                json_output_path_tr = os.path.join(OUTPUT_DIR, f"{filename_base}_risk_results_TR.json")
                comprehensive_json_tr = create_comprehensive_json(results_tr, risk_scorer_tr.schema, language='tr')
                with open(json_output_path_tr, 'w', encoding='utf-8') as f:
                    json.dump(comprehensive_json_tr, f, indent=2, ensure_ascii=False)
            except:
                pass
        
        return True
    
    except Exception as e:
        return False


def main():
    # Ensure output directory exists
    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    
    # Find all JSON files in inputs directory
    input_dir = Path(INPUT_DIR)
    if not input_dir.exists():
        return False
    
    json_files = list(input_dir.glob('*.json'))
    if not json_files:
        return False
    
    # Process each input file
    for input_file in sorted(json_files):
        generate_reports_for_file(str(input_file))
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
