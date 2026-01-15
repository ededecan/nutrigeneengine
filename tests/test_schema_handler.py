"""Tests for schema_handler module"""

import pytest
from nutrigeneengine.schema_handler import SchemaHandler


@pytest.fixture
def sample_schema():
    """Create a sample schema for testing"""
    return {
        "version": "1.0",
        "traits": {
            "Lactose_Intolerance": {
                "domain": "Nutrition",
                "variants": [
                    {"id": "rs4988235", "weight": 2.0, "max_alleles": 2},
                ]
            },
            "Athletic_Performance": {
                "domain": "Performance",
                "variants": [
                    {"id": "rs1815439", "weight": 3.0, "max_alleles": 2}
                ]
            }
        }
    }


def test_schema_handler_initialization(sample_schema):
    """Test SchemaHandler initialization"""
    handler = SchemaHandler(sample_schema)
    assert handler.schema == sample_schema
    assert handler.version == "1.0"


def test_get_traits(sample_schema):
    """Test getting all traits"""
    handler = SchemaHandler(sample_schema)
    traits = handler.get_traits()
    
    assert "Lactose_Intolerance" in traits
    assert "Athletic_Performance" in traits


def test_get_trait(sample_schema):
    """Test getting a specific trait"""
    handler = SchemaHandler(sample_schema)
    trait = handler.get_trait("Lactose_Intolerance")
    
    assert trait is not None
    assert trait["domain"] == "Nutrition"


def test_get_domains(sample_schema):
    """Test getting all domains"""
    handler = SchemaHandler(sample_schema)
    domains = handler.get_domains()
    
    assert "Nutrition" in domains
    assert "Performance" in domains


def test_get_traits_by_domain(sample_schema):
    """Test filtering traits by domain"""
    handler = SchemaHandler(sample_schema)
    nutrition_traits = handler.get_traits_by_domain("Nutrition")
    
    assert "Lactose_Intolerance" in nutrition_traits
    assert "Athletic_Performance" not in nutrition_traits


def test_validate_schema(sample_schema):
    """Test schema validation"""
    handler = SchemaHandler(sample_schema)
    assert handler.validate_schema() is True


def test_validate_invalid_schema():
    """Test validation with invalid schema"""
    invalid_schema = {"version": "1.0"}
    handler = SchemaHandler(invalid_schema)
    
    assert handler.validate_schema() is False
