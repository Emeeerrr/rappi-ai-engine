"""
Metrics Dictionary - Definitions, descriptions, and metadata for all Rappi metrics.

Provides structured metadata for 13 operational metrics used in the analysis.
Each metric includes its name, data type, value range, and business description.
"""

METRICS = {
    "% PRO Users Who Breakeven": {
        "type": "ratio",
        "range": (0, 1),
        "description": "Usuarios Pro cuyo valor generado cubre el costo de membresía / Total usuarios Pro",
        "short_name": "Pro Breakeven",
    },
    "% Restaurants Sessions With Optimal Assortment": {
        "type": "ratio",
        "range": (0, 1),
        "description": "Sesiones con mínimo 40 restaurantes / Total sesiones",
        "short_name": "Optimal Assortment",
    },
    "Gross Profit UE": {
        "type": "currency",
        "range": None,
        "description": "Margen bruto de ganancia / Total órdenes",
        "short_name": "Gross Profit UE",
    },
    "Lead Penetration": {
        "type": "ratio",
        "range": (0, 1),
        "description": "Tiendas habilitadas / (Leads + Habilitadas + Salidas)",
        "short_name": "Lead Penetration",
    },
    "MLTV Top Verticals Adoption": {
        "type": "ratio",
        "range": (0, 1),
        "description": "Usuarios con órdenes en múltiples verticales / Total usuarios",
        "short_name": "Multi-Vertical Adoption",
    },
    "Non-Pro PTC > OP": {
        "type": "ratio",
        "range": (0, 1),
        "description": "Conversión No Pro de Proceed to Checkout a Order Placed",
        "short_name": "Non-Pro Conversion",
    },
    "Perfect Orders": {
        "type": "ratio",
        "range": (0, 1),
        "description": "Órdenes sin cancelaciones/defectos/demora / Total órdenes",
        "short_name": "Perfect Orders",
    },
    "Pro Adoption (Last Week Status)": {
        "type": "ratio",
        "range": (0, 1),
        "description": "Usuarios Pro / Total usuarios Rappi",
        "short_name": "Pro Adoption",
    },
    "Restaurants Markdowns / GMV": {
        "type": "ratio",
        "range": (0, 1),
        "description": "Descuentos restaurantes / GMV Restaurantes",
        "short_name": "Restaurant Markdowns",
    },
    "Restaurants SS > ATC CVR": {
        "type": "ratio",
        "range": (0, 1),
        "description": "Conversión Select Store a Add to Cart",
        "short_name": "Rest SS>ATC CVR",
    },
    "Restaurants SST > SS CVR": {
        "type": "ratio",
        "range": (0, 1),
        "description": "Conversión de seleccionar vertical a seleccionar tienda (Restaurantes)",
        "short_name": "Rest SST>SS CVR",
    },
    "Retail SST > SS CVR": {
        "type": "ratio",
        "range": (0, 1),
        "description": "Conversión de seleccionar vertical a seleccionar tienda (Retail/Supermercados)",
        "short_name": "Retail SST>SS CVR",
    },
    "Turbo Adoption": {
        "type": "ratio",
        "range": (0, 1),
        "description": "Usuarios Turbo / Total usuarios con Turbo disponible",
        "short_name": "Turbo Adoption",
    },
}


def get_metric_context() -> str:
    """Generate a formatted string with all metric definitions for LLM prompts.

    Returns:
        Formatted string describing each metric, suitable for injection
        into system prompts as context.
    """
    lines = ["=== Rappi Operational Metrics Dictionary ===", ""]

    for name, meta in METRICS.items():
        range_str = f"{meta['range'][0]}-{meta['range'][1]}" if meta["range"] else "unbounded"
        lines.append(f"**{name}** ({meta['type']}, {range_str})")
        lines.append(f"  {meta['description']}")
        lines.append("")

    return "\n".join(lines)


def get_metric_names() -> list[str]:
    """Return the list of all metric names."""
    return list(METRICS.keys())


def get_metric_info(metric_name: str) -> dict | None:
    """Get metadata for a specific metric.

    Args:
        metric_name: Exact metric name.

    Returns:
        Metric metadata dict or None if not found.
    """
    return METRICS.get(metric_name)
