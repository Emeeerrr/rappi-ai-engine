"""
Insight Report Generator - Formats insights into structured reports.

This module will implement:
- Report generation in markdown and HTML formats
- Executive summary with top insights
- Per-country and per-metric breakdowns
- Plotly chart embedding for visual reports
- Export to PDF (optional)
"""


def generate_report(insights: list[dict], format: str = "markdown") -> str:
    """Generate a formatted report from a list of insights.

    Args:
        insights: List of insight dictionaries from the analyzer.
        format: Output format ('markdown' or 'html').

    Returns:
        Formatted report string.
    """
    raise NotImplementedError("Report generator not yet implemented")
