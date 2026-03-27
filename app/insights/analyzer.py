"""
Insight Analyzer - Automatic insight generation engine.

This module will implement:
- Detection of significant metric changes (week-over-week, trends)
- Identification of outlier zones and countries
- Cross-metric correlation analysis
- Ranking of insights by business impact
- LLM-powered narrative generation for each insight
"""


def generate_insights(df_metrics, df_orders) -> list[dict]:
    """Analyze data and generate a prioritized list of insights.

    Args:
        df_metrics: DataFrame with zone-level metric data.
        df_orders: DataFrame with order data.

    Returns:
        List of insight dictionaries with keys: title, description,
        metric, severity, affected_zones, recommendation.
    """
    raise NotImplementedError("Insight analyzer not yet implemented")
