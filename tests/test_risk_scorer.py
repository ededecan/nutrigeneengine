"""Tests for risk_scorer module"""

import pytest
from nutrigeneengine.risk_scorer import RiskScorer


@pytest.fixture
def sample_schema():
    """Create a sample schema for testing"""
    return {
        "version": "1.0",
        "traits": {
            "Lactose_Intolerance": {
                "domain": "Nutrition",
                "variants": [
                    {"rsid": "rs4988235", "weight": 2.0, "max_alleles": 2},
                    {"rsid": "rs182549", "weight": 1.5, "max_alleles": 2}
                ]
            },
            "Athletic_Performance": {
                "domain": "Performance",
                "variants": [
                    {"rsid": "rs1815439", "weight": 3.0, "max_alleles": 2}
                ]
            }
        }
    }


def test_risk_scorer_initialization(sample_schema):
    """Test RiskScorer initialization"""
    scorer = RiskScorer(sample_schema)
    assert scorer.schema == sample_schema
    assert scorer.thresholds == [33.0, 66.0]


def test_risk_scorer_custom_thresholds(sample_schema):
    """Test RiskScorer with custom thresholds"""
    scorer = RiskScorer(sample_schema, thresholds=[25.0, 75.0])
    assert scorer.thresholds == [25.0, 75.0]


def test_calculate_score_with_data(sample_schema):
    """Test score calculation with genotype data"""
    scorer = RiskScorer(sample_schema)
    genotype_data = {
        "rs4988235": "AA",  # homozygous
        "rs182549": "AG",   # heterozygous
        "rs1815439": "TG"   # heterozygous
    }
    
    results = scorer.calculate_score(genotype_data)
    
    assert "Lactose_Intolerance" in results
    assert "Athletic_Performance" in results
    assert results["Lactose_Intolerance"]["percentage"] > 0
    assert results["Athletic_Performance"]["percentage"] > 0


def test_calculate_score_missing_data(sample_schema):
    """Test score calculation with missing genotype data"""
    scorer = RiskScorer(sample_schema)
    genotype_data = {
        "rs4988235": "AA"  # homozygous
    }
    
    results = scorer.calculate_score(genotype_data)
    
    assert "Lactose_Intolerance" in results
    assert results["Lactose_Intolerance"]["percentage"] > 0


def test_risk_classification(sample_schema):
    """Test risk classification"""
    scorer = RiskScorer(sample_schema)
    
    assert scorer._classify_risk(20.0) == "LOW"
    assert scorer._classify_risk(50.0) == "MEDIUM"
    assert scorer._classify_risk(80.0) == "HIGH"


def test_set_thresholds(sample_schema):
    """Test threshold modification"""
    scorer = RiskScorer(sample_schema)
    scorer.set_thresholds(25.0, 75.0)
    
    assert scorer.thresholds == [25.0, 75.0]
    assert scorer._classify_risk(50.0) == "MEDIUM"
