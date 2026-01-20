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
            genotype_data: Dictionary with rsid -> diploid genotype (e.g., 'GG', 'GT', 'CC')
        
        Returns:
            Dictionary with calculated scores and classifications
        """
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
    
    
    def _get_allele_count(self, diploid_genotype: str) -> int:
        """
        Get allele count from diploid genotype (e.g., 'GG'->2, 'GT'->1, 'CC'->2).
        Returns allele count based on whether alleles are identical or different.
        """
        if len(diploid_genotype) != 2:
            return 0  # Missing or invalid
        
        # Same alleles = homozygous = 2 alleles
        # Different alleles = heterozygous = 1 allele
        if diploid_genotype[0] == diploid_genotype[1]:
            return 2
        else:
            return 1
    
    def _process_group(self, group_data: Dict[str, Any], genotype_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Recursively process hierarchical groups.
        Adds group_name to each result for proper categorization in visualizations.
        """
        results = {}
        group_name = group_data.get('name', 'Unknown')
        
        for trait in group_data.get('traits', []):
            if 'subtraits' in trait:
                # Process subtraits
                for subtrait in trait['subtraits']:
                    result = self._calculate_trait_score(
                        subtrait['name'], 
                        subtrait, 
                        genotype_data
                    )
                    result['group_name'] = group_name  # Add group name for categorization
                    results[subtrait['name']] = result
            elif 'variants' in trait:
                # Process direct trait
                result = self._calculate_trait_score(
                    trait['name'], 
                    trait, 
                    genotype_data
                )
                result['group_name'] = group_name  # Add group name for categorization
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
        Works directly with diploid genotypes (GG, GT, CC, etc).
        Handles risk_up, risk_down, contextual, and neutral variants.
        """
        variants = trait_info.get("variants", [])
        score = 0.0
        max_possible_with_data = 0.0
        variant_details = []
        
        for variant in variants:
            rsid = variant.get("rsid")
            weight = variant.get("weight", 1.0)
            
            # Get effect direction (default: risk_up for backward compatibility)
            effect = variant.get("effect", {})
            direction = effect.get("direction", "risk_up")
            
            # Skip neutral variants (they don't contribute to risk score)
            if direction == "neutral":
                variant_details.append(f"{rsid}: Neutral (phenotypic only, not scored)")
                continue
            
            # Support genotype point mapping
            if 'scoring' in variant and 'genotype_points' in variant['scoring']:
                weight = variant['scoring'].get('default_weight', 1.0)
                point_map = variant['scoring']['genotype_points']
                
                # Get diploid genotype (e.g., 'GG', 'GT', 'CC')
                diploid = genotype_data.get(rsid, None)
                
                if not diploid or len(diploid) != 2:
                    variant_details.append(f"{rsid}: Missing")
                    continue
                
                # Get allele count and map to points
                allele_count = self._get_allele_count(diploid)
                points = point_map.get(str(allele_count), 0)
                
                # Apply direction-specific scoring
                if direction == "risk_up":
                    # Standard: more alternate alleles = higher risk
                    trait_score = points * weight
                    
                elif direction == "risk_down":
                    # Inverted: fewer alternate alleles = higher risk (more favorable = lower score)
                    # Invert the points: (2 - points)
                    inverted_points = (2 - points) if points in [0, 1, 2] else 0
                    trait_score = inverted_points * weight
                    
                elif direction == "contextual":
                    # Neutral scoring: no directional bias
                    trait_score = points * weight
                else:
                    trait_score = 0
                
                score += trait_score
                max_possible_with_data += 2 * weight
                
                # Enhanced detail reporting
                direction_label = f"[{direction.upper()}]"
                variant_details.append(
                    f"{rsid} ({diploid}): {allele_count} alleles → {points} points "
                    f"({direction_label}) × {weight}w = {trait_score}"
                )
            else:
                # Standard format with weight (legacy support)
                diploid = genotype_data.get(rsid, None)
                if not diploid or len(diploid) != 2:
                    continue
                
                # Get allele count from diploid
                allele_count = self._get_allele_count(diploid)
                
                # Apply direction-specific scoring
                if direction == "risk_up":
                    trait_score = allele_count * weight
                elif direction == "risk_down":
                    trait_score = (2 - allele_count) * weight
                elif direction == "contextual":
                    trait_score = allele_count * weight
                else:
                    trait_score = 0
                
                score += trait_score
                max_possible_with_data += 2 * weight
                
                direction_label = f"[{direction.upper()}]"
                variant_details.append(
                    f"{rsid} ({diploid}): {allele_count} alleles ({direction_label}) × {weight} = {trait_score}"
                )
        
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
