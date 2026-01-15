"""
NutriGeneEngine: A schema-driven genetic risk assessment engine.

This module provides tools for calculating, classifying, and visualizing
personalized genetic risk scores for nutrition, athletic performance, and
behavioral traits.
"""

__version__ = "1.0.0"
__author__ = "Enes Dedecan"

from .risk_scorer import RiskScorer
from .schema_handler import SchemaHandler
from .visualizer import Visualizer
from .pdf_generator import PDFReportGenerator

__all__ = ["RiskScorer", "SchemaHandler", "Visualizer", "PDFReportGenerator"]
