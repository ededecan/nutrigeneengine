# NutriGeneEngine

A lightweight, schema-driven Python engine designed to calculate, classify, and visualize personalized genetic risk scores for nutrition, athletic performance, and behavioral traits.

## Features

### Dynamic Risk Scoring
Calculates weighted polygenic risk scores based on a flexible JSON schema (traits, variants, weights) and user genotype data.

### Smart Normalization
Automatically handles missing genetic data by adjusting the "maximum possible score" to ensure accurate percentage calculations (0–100%).

### Risk Classification
Categorizes scores into actionable levels (Low, Medium, High) based on configurable thresholds (default: 33% / 66%).

### Visual Reporting
Generates professional-grade visualizations:
- **Summary Dashboard**: A high-level ranking of all traits to identify top risks immediately.
- **Domain-Specific Charts**: Separate graphs for Nutrition, Performance, and Lifestyle for focused analysis.

## Installation

### Using pip

```bash
pip install matplotlib numpy
pip install -e .
```

### Using Poetry

```bash
poetry install
```

## Dependencies

- **matplotlib**: Required for generating the risk assessment charts
- **numpy**: Required for numerical operations during graph plotting
- **Standard Library**: `json` (for data parsing)

## Quick Start

```python
from nutrigeneengine import RiskAssessment

# Initialize with schema
assessment = RiskAssessment(schema_path="schema.json")

# Load user genotype data
user_data = assessment.load_genotype("user_profile.json")

# Calculate risk scores
results = assessment.calculate_risk(user_data)

# Generate visualizations
assessment.plot_summary_dashboard()
assessment.plot_domain_charts()

# Export results
assessment.export_results("output_results.json")
```

## Project Structure

```
NutriGeneEngine/
├── src/nutrigeneengine/
│   ├── __init__.py
│   ├── risk_scorer.py          # Core risk scoring logic
│   ├── schema_handler.py        # Schema parsing and validation
│   ├── visualizer.py            # Chart generation
│   └── utils.py                 # Helper functions
├── tests/
│   ├── test_risk_scorer.py
│   ├── test_schema_handler.py
│   └── test_visualizer.py
├── pyproject.toml
├── setup.py
├── README.md
└── LICENSE
```

## Development

### Running Tests

```bash
pytest
```

### Code Quality Checks

```bash
black .
isort .
flake8 .
mypy .
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Author

Enes Dedecan

