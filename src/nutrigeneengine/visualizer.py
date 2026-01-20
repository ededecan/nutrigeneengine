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
        language: Language for labels ('en' or 'tr')
    """
    
    # Label translations
    LABELS = {
        'en': {
            'risk_score': 'Risk Percentage (%)',
            'overall_summary': 'Overall Genetic Risk Summary',
            'low_risk': 'Low Risk (0-33)',
            'medium_risk': 'Medium Risk (34-66)',
            'high_risk': 'High Risk (67-100)',
            'risk_factors': 'Risk Factors'
        },
        'tr': {
            'risk_score': 'Risk Oranı (0-100)',
            'overall_summary': 'Genel Risk Özeti',
            'low_risk': 'Düşük Risk (0-33)',
            'medium_risk': 'Orta Risk (34-66)',
            'high_risk': 'Yüksek Risk (67-100)',
            'risk_factors': 'Risk Faktörleri'
        }
    }
    
    def __init__(self, results: Dict[str, Any], schema: Optional[Dict[str, Any]] = None, language: str = 'en'):
        """
        Initialize the visualizer.
        
        Args:
            results: Dictionary of calculated risk scores
            schema: Optional schema for domain information
            language: 'en' for English or 'tr' for Turkish
        """
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError("matplotlib is required for visualization. "
                            "Install it with: pip install matplotlib")
        
        self.results = results
        self.schema = schema or {}
        self.language = language
        self.labels = self.LABELS.get(language, self.LABELS['en'])
    
    def plot_summary_dashboard(self, output_path: Optional[str] = None) -> None:
        """
        Generate a summary dashboard showing all traits ranked by risk.
        Filters out Informational/Bilgilendirici traits.
        Uses language-appropriate labels (English or Turkish).
        
        Args:
            output_path: Optional path to save the figure
        """
        import matplotlib.pyplot as plt
        import numpy as np
        
        # Filter out informational traits
        filtered_results = {k: v for k, v in self.results.items() 
                          if k not in ['Informational', 'Bilgilendirici']}
        
        traits = sorted(
            filtered_results.items(),
            key=lambda x: x[1].get("percentage", 0),
            reverse=True
        )
        
        trait_names = [t[0] for t in traits]
        percentages = [t[1].get("percentage", 0) for t in traits]
        colors_list = [self._get_color_for_percentage(p) for p in percentages]
        
        fig, ax = plt.subplots(figsize=(12, 8))
        bars = ax.barh(trait_names, percentages, color=colors_list)
        
        ax.set_xlabel(self.labels['risk_score'], fontsize=12, fontweight="bold")
        ax.set_title(self.labels['overall_summary'], fontsize=14, fontweight="bold")
        ax.set_xlim(0, 100)
        
        # Add percentage labels on bars
        for i, (bar, pct) in enumerate(zip(bars, percentages)):
            ax.text(pct + 1, i, f"{pct:.1f}%", va="center", fontweight="bold")
        
        # Add threshold lines
        ax.axvline(x=33, color='gray', linestyle=':', linewidth=1)
        ax.axvline(x=66, color='gray', linestyle=':', linewidth=1)
        
        # Legend with language-appropriate labels
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#4CAF50', label=self.labels['low_risk']),
            Patch(facecolor='#FFC107', label=self.labels['medium_risk']),
            Patch(facecolor='#F44336', label=self.labels['high_risk'])
        ]
        ax.legend(handles=legend_elements, loc='lower right')
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
        else:
            plt.show()
        
        plt.close()
    
    def plot_domain_charts(self, output_dir: Optional[str] = None, filename_base: Optional[str] = None, 
                          suffix: str = "") -> None:
        """
        Generate separate charts for each domain/group.
        Filters out Informational/Bilgilendirici traits and organizes by group_name from results.
        
        Args:
            output_dir: Optional directory to save the figures
            filename_base: Optional base filename for output (used with _group_risk_graphs suffix)
            suffix: Optional suffix for filename (e.g., '_TR' for Turkish)
        """
        # Filter out informational traits
        filtered_results = {k: v for k, v in self.results.items() 
                          if k not in ['Informational', 'Bilgilendirici']}
        
        # Group results by group_name from the results themselves
        groups_data = {}
        for trait_name, result in filtered_results.items():
            group_name = result.get('group_name', 'Unknown')
            if group_name not in groups_data:
                groups_data[group_name] = []
            groups_data[group_name].append((trait_name, result))
        
        if not groups_data:
            return
        
        # Create a chart for each group
        num_groups = len(groups_data)
        fig, axes = plt.subplots(nrows=num_groups, ncols=1, figsize=(10, 5 * num_groups))
        if num_groups == 1:
            axes = [axes]
        
        for ax, (group_name, traits) in zip(axes, sorted(groups_data.items())):
            # Sort traits in descending order by percentage (highest risk first)
            sorted_traits = sorted(traits, key=lambda x: x[1]["percentage"], reverse=True)
            trait_names = [t[0] for t in sorted_traits]
            percentages = [t[1]["percentage"] for t in sorted_traits]
            colors = [self._get_color_for_percentage(p) for p in percentages]
            
            y_pos = np.arange(len(trait_names))
            ax.barh(y_pos, percentages, color=colors, height=0.6)
            ax.set_yticks(y_pos)
            ax.set_yticklabels(trait_names)
            ax.set_xlim(0, 100)
            ax.set_xlabel(self.labels['risk_score'], fontsize=11, fontweight="bold")
            ax.set_title(f"{self.labels['risk_factors']}: {group_name}", fontsize=12, fontweight="bold")
            ax.grid(axis='x', linestyle='--', alpha=0.7)
            
            # Add threshold lines
            ax.axvline(x=33, color='gray', linestyle=':', linewidth=1)
            ax.axvline(x=66, color='gray', linestyle=':', linewidth=1)
        
        plt.tight_layout()
        
        if output_dir:
            if filename_base:
                filename = f"{output_dir}/{filename_base}_group_risk_graphs{suffix}.png"
            else:
                filename = f"{output_dir}/group_risk_graphs{suffix}.png"
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
