"""
Utility Functions

Helper functions for data processing and validation.
"""

import json
from typing import Dict, Any, Optional


def load_json_file(filepath: str) -> Dict[str, Any]:
    """
    Load JSON data from file.
    
    Args:
        filepath: Path to the JSON file
    
    Returns:
        Dictionary containing the JSON data
    """
    with open(filepath, 'r') as f:
        return json.load(f)


def save_json_file(data: Dict[str, Any], filepath: str, indent: int = 2) -> None:
    """
    Save data to JSON file.
    
    Args:
        data: Dictionary to save
        filepath: Path where to save the file
        indent: JSON indentation level
    """
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=indent)


def validate_genotype_data(genotype_data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate genotype data against schema.
    
    Args:
        genotype_data: Genotype data to validate
        schema: Schema to validate against
    
    Returns:
        True if valid, False otherwise
    """
    valid_variant_ids = set()
    
    for trait_info in schema.get("traits", {}).values():
        for variant in trait_info.get("variants", []):
            valid_variant_ids.add(variant.get("id"))
    
    for variant_id in genotype_data.keys():
        if variant_id not in valid_variant_ids:
            return False
    
    return True


def merge_results(results1: Dict[str, Any], results2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two result dictionaries.
    
    Args:
        results1: First results dictionary
        results2: Second results dictionary
    
    Returns:
        Merged results dictionary
    """
    merged = results1.copy()
    merged.update(results2)
    return merged


def filter_results_by_domain(results: Dict[str, Any], domain: str) -> Dict[str, Any]:
    """
    Filter results by domain.
    
    Args:
        results: Results dictionary
        domain: Domain to filter by
    
    Returns:
        Filtered results dictionary
    """
    return {
        trait: result
        for trait, result in results.items()
        if result.get("domain") == domain
    }


def get_high_risk_traits(results: Dict[str, Any], threshold: float = 66.0) -> Dict[str, Any]:
    """
    Get traits with high risk classification.
    
    Args:
        results: Results dictionary
        threshold: Percentage threshold for high risk
    
    Returns:
        Dictionary of high-risk traits
    """
    return {
        trait: result
        for trait, result in results.items()
        if result.get("percentage", 0) >= threshold
    }
