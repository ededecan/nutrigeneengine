"""
Risk Scoring Module

Calculates weighted polygenic risk scores based on JSON schema and genotype data.
Uses zygosity format (wt/het/hom) exclusively.
Handles hierarchical and flat trait structures.
"""

import json
from typing import Dict, List, Any, Optional


class RiskScorer:
    """
    Calculates genetic risk scores based on schema and genotype data.
    Uses zygosity scoring (wt/het/hom).
    
    Attributes:
        schema: Dictionary containing trait definitions and weights
        thresholds: Risk classification thresholds (default: [33, 66])
        language: Output language ('en' or 'tr')
    """
    
    RISK_LABELS = {
        'en': {'low': 'LOW', 'medium': 'MEDIUM', 'high': 'HIGH'},
        'tr': {'low': 'DÜŞÜK', 'medium': 'ORTA', 'high': 'YÜKSEK'}
    }
    
    def __init__(self, schema: Dict[str, Any], thresholds: Optional[List[float]] = None, language: str = 'en'):
        """
        Initialize the risk scorer.
        
        Args:
            schema: Dictionary with trait and variant information
            thresholds: List of two thresholds for Low/Medium/High classification
            language: 'en' for English or 'tr' for Turkish
        """
        self.schema = schema
        self.thresholds = thresholds or [33.0, 66.0]
        self.language = language
    
    @classmethod
    def from_file(cls, schema_path: str, thresholds: Optional[List[float]] = None, language: str = 'en'):
        """Load schema from JSON file."""
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        return cls(schema, thresholds, language)
    
    def calculate_score(self, genotype_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Calculate risk scores for all traits.
        
        Args:
            genotype_data: Dictionary with rsid -> zygosity (wt/het/hom) or diploid (GT/AC/CC) pairs
        
        Returns:
            Dictionary with calculated scores and classifications
        """
        # Convert diploid to zygosity if needed
        genotype_data = self._ensure_zygosity_format(genotype_data)
        
        results = {}
        
        # Handle hierarchical schema.
        if 'taxonomy' in self.schema:
            for group in self.schema.get('taxonomy', {}).get('top_groups', []):
                results.update(self._process_group(group, genotype_data))
        # Handle flat schema
        else:
            for trait_name, trait_info in self.schema.get("traits", {}).items():
                result = self._calculate_trait_score(trait_name, trait_info, genotype_data)
                results[trait_name] = result
        
        return results
    
    
    def _ensure_zygosity_format(self, genotype_data: Dict[str, str]) -> Dict[str, str]:
        """
        Convert diploid format (GT, AC, CC) to zygosity (wt, het, hom) if needed.
        Also supports direct zygosity format.
        """
        if not genotype_data:
            return genotype_data
        
        first_value = next(iter(genotype_data.values()), None)
        
        # Already zygosity format
        if first_value in ('wt', 'het', 'hom', 'missing'):
            return genotype_data
        
        # Convert diploid to zygosity
        converted = {}
        for rsid, genotype in genotype_data.items():
            if len(genotype) == 2:
                if genotype[0] == genotype[1]:
                    converted[rsid] = 'hom'  # Homozygous
                else:
                    converted[rsid] = 'het'  # Heterozygous
            else:
                # Can't determine, skip
                converted[rsid] = 'missing'
        
        return converted
    
    def _process_group(self, group_data: Dict[str, Any], genotype_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Recursively process hierarchical groups.
        """
        results = {}
        
        for trait in group_data.get('traits', []):
            if 'subtraits' in trait:
                # Process subtraits
                for subtrait in trait['subtraits']:
                    result = self._calculate_trait_score(
                        subtrait['name'], 
                        subtrait, 
                        genotype_data
                    )
                    results[subtrait['name']] = result
            elif 'variants' in trait:
                # Process direct trait
                result = self._calculate_trait_score(
                    trait['name'], 
                    trait, 
                    genotype_data
                )
                results[trait['name']] = result
        
        return results
    
    def _calculate_trait_score(
        self,
        trait_name: str,
        trait_info: Dict[str, Any],
        genotype_data: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Calculate score for a single trait.
        Uses zygosity point mapping (wt/het/hom).
        """
        variants = trait_info.get("variants", [])
        score = 0.0
        max_possible_with_data = 0.0
        variant_details = []
        
        for variant in variants:
            rsid = variant.get("rsid")
            weight = variant.get("weight", 1.0)
            
            # Support genotype point mapping
            if 'scoring' in variant and 'genotype_points' in variant['scoring']:
                weight = variant['scoring'].get('default_weight', 1.0)
                point_map = variant['scoring']['genotype_points']
                
                # Get zygosity value (wt/het/hom)
                zygosity = genotype_data.get(rsid, "missing")
                
                if zygosity == "missing":
                    variant_details.append(f"{rsid}: Missing")
                    continue
                
                # Map zygosity to points
                points = point_map.get(zygosity, 0)
                trait_score = points * weight
                score += trait_score
                max_possible_with_data += 2 * weight  # Max 2 alleles
                variant_details.append(f"{rsid} ({zygosity}): {points} × {weight} = {trait_score}")
            else:
                # Standard format with weight
                zygosity = genotype_data.get(rsid, "missing")
                if zygosity == "missing":
                    continue
                
                # Map zygosity to allele count: wt=0, het=1, hom=2
                zygosity_map = {'wt': 0, 'het': 1, 'hom': 2}
                allele_count = zygosity_map.get(zygosity, 0)
                
                trait_score = allele_count * weight
                score += trait_score
                max_possible_with_data += 2 * weight
                variant_details.append(f"{rsid} ({zygosity}): {allele_count} × {weight} = {trait_score}")
        
        # Smart normalization
        if max_possible_with_data > 0:
            percentage = (score / max_possible_with_data) * 100
        else:
            percentage = 0.0
        
        classification = self._classify_risk(percentage)
        
        return {
            "name": trait_name,
            "normalized_score": round(percentage, 1),
            "score": score,
            "max_possible_score": max_possible_with_data,
            "percentage": round(percentage, 2),
            "classification": classification,
            "domain": trait_info.get("domain", "Unknown"),
            "details": variant_details
        }
    
    def _classify_risk(self, percentage: float) -> str:
        """
        Classify risk level based on percentage.
        Returns localized label based on language setting.
        """
        if percentage < self.thresholds[0]:
            risk_level = 'low'
        elif percentage < self.thresholds[1]:
            risk_level = 'medium'
        else:
            risk_level = 'high'
        
        return self.RISK_LABELS.get(self.language, self.RISK_LABELS['en']).get(risk_level, 'LOW')
    
    def set_thresholds(self, low_threshold: float, high_threshold: float) -> None:
        """Update risk classification thresholds."""
        self.thresholds = [low_threshold, high_threshold]
    
    def set_language(self, language: str) -> None:
        """Set output language ('en' or 'tr')."""
        if language in self.RISK_LABELS:
            self.language = language
