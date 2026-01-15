#!/usr/bin/env python3
"""
NutriGeneEngine - Full Report Generation
Reads from inputs/ folder, outputs to outputs/ folder
"""

import json
import sys
import os
from pathlib import Path

# Get the directory of this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Configuration
SCHEMA_FILENAME = os.path.join(SCRIPT_DIR, 'src/nutrigeneengine/schema.json')
SCHEMA_TR_FILENAME = os.path.join(SCRIPT_DIR, 'src/nutrigeneengine/schema_tr.json')
INPUT_DIR = os.path.join(SCRIPT_DIR, 'inputs')
OUTPUT_DIR = os.path.join(SCRIPT_DIR, 'outputs')

# Import from risk_assessment functions
sys.path.insert(0, os.path.dirname(__file__))
from risk_assessment import (
    calculate_normalized_risk, process_group, create_summary_graph,
    create_group_graphs, create_turkish_summary_graph, create_turkish_group_graphs,
    save_results_to_json, generate_pdf_report
)


def load_schema(schema_path):
    """Load schema from file"""
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Schema file '{schema_path}' not found.")
        return None


def generate_reports_for_file(input_file):
    """Generate all reports for a given input file"""
    
    # Load schema
    print(f"\n[1/2] Loading schema from {SCHEMA_FILENAME}...")
    schema = load_schema(SCHEMA_FILENAME)
    if schema is None:
        return False
    print(f"      ✓ Schema loaded")
    
    # Load Turkish schema
    schema_tr = None
    if Path(SCHEMA_TR_FILENAME).exists():
        schema_tr = load_schema(SCHEMA_TR_FILENAME)
    
    # Load genotypes from input file
    print(f"[2/2] Loading genotypes from {input_file}...")
    try:
        with open(input_file, 'r') as f:
            user_data = json.load(f)
        user_genome = user_data['genotypes']
        print(f"      ✓ Genotypes loaded: {len(user_genome)} variants")
    except (FileNotFoundError, KeyError) as e:
        print(f"ERROR: Could not load genotypes: {e}")
        return False
    
    # Get just the filename (without path)
    filename_base = Path(input_file).stem
    
    # Change to output directory for file generation
    original_dir = os.getcwd()
    os.chdir(OUTPUT_DIR)
    
    try:
        # Generate English reports
        print(f"\n[3/4] Calculating risk scores (English)...")
        all_results = []
        for group in schema['taxonomy']['top_groups']:
            group_results = process_group(group, user_genome, is_turkish=False)
            all_results.extend(group_results)
        print(f"      ✓ Calculated {len(all_results)} traits")
        
        print(f"[4/4] Generating outputs...")
        create_summary_graph(all_results, f'{filename_base}.json')
        create_group_graphs(all_results, f'{filename_base}.json')
        save_results_to_json(all_results, f'{filename_base}.json')
        generate_pdf_report(all_results, f'{filename_base}.json', schema)
        print(f"      ✓ English reports generated")
        
        # Generate Turkish reports if schema available
        if schema_tr:
            print(f"[4/4] Generating Turkish outputs...")
            all_results_tr = []
            for group in schema_tr['taxonomy']['top_groups']:
                group_results = process_group(group, user_genome, is_turkish=True)
                all_results_tr.extend(group_results)
            
            create_turkish_summary_graph(all_results_tr, f'{filename_base}.json', schema_tr)
            create_turkish_group_graphs(all_results_tr, f'{filename_base}.json', schema_tr)
            generate_pdf_report(all_results_tr, f'{filename_base}.json', schema_tr, is_turkish=True)
            print(f"      ✓ Turkish reports generated")
        
        return True
    
    finally:
        os.chdir(original_dir)


def main():
    # Ensure output directory exists
    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    
    print("=" * 70)
    print("NutriGeneEngine: Full Report Generation")
    print("=" * 70)
    
    # Find all JSON files in inputs directory
    input_dir = Path(INPUT_DIR)
    if not input_dir.exists():
        print(f"ERROR: Input directory '{INPUT_DIR}' not found")
        return False
    
    json_files = list(input_dir.glob('*.json'))
    if not json_files:
        print(f"ERROR: No JSON files found in '{INPUT_DIR}'")
        return False
    
    # Process each input file
    for input_file in sorted(json_files):
        print(f"\nProcessing {input_file.name}...")
        generate_reports_for_file(str(input_file))
    
    print("\n" + "=" * 70)
    print("Report Generation Complete!")
    print("=" * 70)
    
    # List generated files
    output_files = list(Path(OUTPUT_DIR).glob('*_report*.pdf'))
    print(f"\nGenerated PDFs:")
    for pdf in sorted(output_files):
        print(f"  • {pdf.name}")
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
