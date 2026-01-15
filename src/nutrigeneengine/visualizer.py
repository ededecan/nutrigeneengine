"""
Visualization Module

Generates professional-grade charts and reports for risk assessment results.
"""

from typing import Dict, Any, Optional, List
import json

try:
    import matplotlib.pyplot as plt
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class Visualizer:
    """
    Generates visualizations for risk assessment results.
    
    Attributes:
        results: Dictionary of risk assessment results
        schema: Schema information for domain mapping
    """
    
    def __init__(self, results: Dict[str, Any], schema: Optional[Dict[str, Any]] = None):
        """
        Initialize the visualizer.
        
        Args:
            results: Dictionary of calculated risk scores
            schema: Optional schema for domain information
        """
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError("matplotlib is required for visualization. "
                            "Install it with: pip install matplotlib")
        
        self.results = results
        self.schema = schema or {}
    
    def plot_summary_dashboard(self, output_path: Optional[str] = None) -> None:
        """
        Generate a summary dashboard showing all traits ranked by risk.
        
        Args:
            output_path: Optional path to save the figure
        """
        import matplotlib.pyplot as plt
        import numpy as np
        
        traits = sorted(
            self.results.items(),
            key=lambda x: x[1].get("percentage", 0),
            reverse=True
        )
        
        trait_names = [t[0] for t in traits]
        percentages = [t[1].get("percentage", 0) for t in traits]
        colors_list = [self._get_color_for_percentage(p) for p in percentages]
        
        fig, ax = plt.subplots(figsize=(12, 8))
        bars = ax.barh(trait_names, percentages, color=colors_list)
        
        ax.set_xlabel("Risk Percentage (%)", fontsize=12, fontweight="bold")
        ax.set_title("Overall Genetic Risk Summary", fontsize=14, fontweight="bold")
        ax.set_xlim(0, 100)
        
        # Add percentage labels on bars
        for i, (bar, pct) in enumerate(zip(bars, percentages)):
            ax.text(pct + 1, i, f"{pct:.1f}%", va="center", fontweight="bold")
        
        # Add threshold lines
        ax.axvline(x=33, color='gray', linestyle=':', linewidth=1)
        ax.axvline(x=66, color='gray', linestyle=':', linewidth=1)
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
        else:
            plt.show()
        
        plt.close()
    
    def plot_domain_charts(self, output_dir: Optional[str] = None) -> None:
        """
        Generate separate charts for each domain.
        
        Args:
            output_dir: Optional directory to save the figures
        """
        # Group results by domain
        domain_results = {}
        for trait_name, result in self.results.items():
            domain = result.get("domain", "Unknown")
            if domain not in domain_results:
                domain_results[domain] = {}
            domain_results[domain][trait_name] = result
        
        # Create a chart for each domain
        for domain, traits in domain_results.items():
            self._plot_domain_chart(domain, traits, output_dir)
    
    def _plot_domain_chart(self, domain: str, traits: Dict[str, Any], 
                          output_dir: Optional[str] = None) -> None:
        """Generate a chart for a specific domain."""
        trait_names = list(traits.keys())
        percentages = [traits[t]["percentage"] for t in trait_names]
        colors = [self._get_color_for_percentage(p) for p in percentages]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(range(len(trait_names)), percentages, color=colors)
        
        ax.set_xticks(range(len(trait_names)))
        ax.set_xticklabels(trait_names, rotation=45, ha="right")
        ax.set_ylabel("Risk Percentage (%)", fontsize=12, fontweight="bold")
        ax.set_title(f"{domain} - Genetic Risk Assessment", 
                    fontsize=14, fontweight="bold")
        ax.set_ylim(0, 100)
        
        # Add percentage labels on bars
        for bar, pct in zip(bars, percentages):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 2,
                   f"{pct:.1f}%", ha="center", va="bottom", fontweight="bold")
        
        plt.tight_layout()
        
        if output_dir:
            filename = f"{output_dir}/{domain.replace(' ', '_')}_risk_chart.png"
            plt.savefig(filename, dpi=300, bbox_inches="tight")
        else:
            plt.show()
        
        plt.close()
    
    @staticmethod
    def _get_color_for_percentage(percentage: float) -> str:
        """
        Get color based on risk percentage.
        
        Args:
            percentage: Risk percentage (0-100)
        
        Returns:
            Color code (green for low, yellow for medium, red for high)
        """
        if percentage < 33:
            return "#2ecc71"  # Green
        elif percentage < 66:
            return "#f39c12"  # Orange
        else:
            return "#e74c3c"  # Red
    
    def export_results_to_json(self, output_path: str) -> None:
        """Export results to JSON file."""
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)
    
    def export_results_to_csv(self, output_path: str) -> None:
        """Export results to CSV file."""
        import csv
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                "Trait", "Score", "Max Possible Score", "Percentage", 
                "Classification", "Domain"
            ])
            writer.writeheader()
            
            for trait_name, result in self.results.items():
                writer.writerow({
                    "Trait": trait_name,
                    "Score": result.get("score", "N/A"),
                    "Max Possible Score": result.get("max_possible_score", "N/A"),
                    "Percentage": result.get("percentage", "N/A"),
                    "Classification": result.get("classification", "N/A"),
                    "Domain": result.get("domain", "N/A")
                })
