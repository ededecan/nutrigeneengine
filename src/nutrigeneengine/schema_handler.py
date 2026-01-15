"""
Schema Handler Module

Handles loading, validation, and manipulation of genetic risk assessment schemas.
"""

import json
from typing import Dict, Any, Optional, List


class SchemaHandler:
    """
    Manages schema loading, validation, and manipulation.
    
    Attributes:
        schema: Dictionary containing the schema data
        version: Schema version
    """
    
    def __init__(self, schema: Dict[str, Any]):
        """
        Initialize the schema handler.
        
        Args:
            schema: Dictionary containing trait and variant definitions
        """
        self.schema = schema
        self.version = schema.get("version", "1.0")
    
    @classmethod
    def from_file(cls, schema_path: str):
        """Load schema from a JSON file."""
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        return cls(schema)
    
    def get_traits(self) -> Dict[str, Dict[str, Any]]:
        """Get all traits defined in the schema."""
        return self.schema.get("traits", {})
    
    def get_trait(self, trait_name: str) -> Optional[Dict[str, Any]]:
        """Get information for a specific trait."""
        return self.schema.get("traits", {}).get(trait_name)
    
    def get_variants_for_trait(self, trait_name: str) -> list:
        """Get all variants for a specific trait."""
        trait = self.get_trait(trait_name)
        if trait:
            return trait.get("variants", [])
        return []
    
    def get_domains(self) -> set:
        """Get all unique domains in the schema."""
        domains = set()
        for trait_info in self.schema.get("traits", {}).values():
            domain = trait_info.get("domain")
            if domain:
                domains.add(domain)
        return domains
    
    def get_traits_by_domain(self, domain: str) -> Dict[str, Dict[str, Any]]:
        """Get all traits belonging to a specific domain."""
        result = {}
        for trait_name, trait_info in self.schema.get("traits", {}).items():
            if trait_info.get("domain") == domain:
                result[trait_name] = trait_info
        return result
    
    def validate_schema(self) -> bool:
        """
        Validate schema structure.
        
        Returns:
            True if schema is valid, False otherwise
        """
        required_keys = ["traits"]
        
        if not all(key in self.schema for key in required_keys):
            return False
        
        for trait_name, trait_info in self.schema["traits"].items():
            if "variants" not in trait_info:
                return False
            
            for variant in trait_info["variants"]:
                required_variant_keys = ["id", "weight"]
                if not all(key in variant for key in required_variant_keys):
                    return False
        
        return True
    
    def save_schema(self, output_path: str) -> None:
        """Save the current schema to a JSON file."""
        with open(output_path, 'w') as f:
            json.dump(self.schema, f, indent=2)
    
    def translate_schema(self, translation_map: Dict[str, str]) -> 'SchemaHandler':
        """
        Create a translated copy of the schema.
        
        Args:
            translation_map: Dictionary mapping original names to translations
        
        Returns:
            New SchemaHandler with translated schema
        """
        translated_schema = json.loads(json.dumps(self.schema))
        
        # Translate trait names and descriptions
        translated_traits = {}
        for trait_name, trait_info in translated_schema.get("traits", {}).items():
            translated_name = translation_map.get(trait_name, trait_name)
            translated_traits[translated_name] = trait_info
        
        translated_schema["traits"] = translated_traits
        
        return SchemaHandler(translated_schema)
    
    def get_trait_info(self, trait_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a trait including gene and study details.
        Searches both flat and hierarchical schema structures.
        """
        # Check flat schema first
        if trait_name in self.schema.get("traits", {}):
            return self.schema["traits"][trait_name]
        
        # Check hierarchical schema
        for group in self.schema.get("taxonomy", {}).get("top_groups", []):
            for trait in group.get("traits", []):
                if trait.get("name") == trait_name:
                    return trait
                for subtrait in trait.get("subtraits", []):
                    if subtrait.get("name") == trait_name:
                        return subtrait
        
        return None
    
    def get_variant_details(self, rsid: str) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific variant (RSID) including gene and studies.
        """
        # Search all traits for the variant
        for group in self.schema.get("taxonomy", {}).get("top_groups", []):
            for trait in group.get("traits", []):
                for variant in trait.get("variants", []):
                    if variant.get("rsid") == rsid or variant.get("id") == rsid:
                        return variant
                for subtrait in trait.get("subtraits", []):
                    for variant in subtrait.get("variants", []):
                        if variant.get("rsid") == rsid or variant.get("id") == rsid:
                            return variant
        
        # Check flat schema
        for trait in self.schema.get("traits", {}).values():
            for variant in trait.get("variants", []):
                if variant.get("rsid") == rsid or variant.get("id") == rsid:
                    return variant
        
        return None
    
    def get_hierarchy(self) -> Dict[str, List[str]]:
        """
        Get hierarchical structure of traits (groups -> traits -> subtraits).
        Returns a dictionary for easy traversal.
        """
        hierarchy = {}
        
        for group in self.schema.get("taxonomy", {}).get("top_groups", []):
            group_name = group.get("name")
            hierarchy[group_name] = []
            
            for trait in group.get("traits", []):
                if "subtraits" in trait:
                    for subtrait in trait["subtraits"]:
                        hierarchy[group_name].append(subtrait.get("name"))
                else:
                    hierarchy[group_name].append(trait.get("name"))
        
        return hierarchy
