"""
Data Loader - Load, validate, and export Rappi operational data from Excel.

Handles three sheets:
- RAW_INPUT_METRICS: Zone-level metrics across 9 weeks (12573 rows)
- RAW_ORDERS: Order data across 9 weeks (1242 rows)
- RAW_SUMMARY: Descriptive metadata
"""

import logging
from pathlib import Path

import pandas as pd

from app.config import DATA_RAW_DIR, DATA_PROCESSED_DIR, WEEK_COLUMNS_METRICS, WEEK_COLUMNS_ORDERS

logger = logging.getLogger(__name__)

# Module-level cache
_data_cache: dict[str, pd.DataFrame] = {}

EXPECTED_COLS_METRICS = [
    "COUNTRY", "CITY", "ZONE", "ZONE_TYPE", "ZONE_PRIORITIZATION",
    "METRIC", *WEEK_COLUMNS_METRICS,
]

EXPECTED_COLS_ORDERS = [
    "COUNTRY", "CITY", "ZONE", "METRIC", *WEEK_COLUMNS_ORDERS,
]


def load_raw_data(xlsx_path: str | Path | None = None) -> dict[str, pd.DataFrame]:
    """Load the three sheets from the Rappi Excel file.

    Args:
        xlsx_path: Path to the .xlsx file. If None, looks for the first
                   .xlsx file in data/raw/.

    Returns:
        Dict with keys 'metrics', 'orders', 'summary' mapping to DataFrames.

    Raises:
        FileNotFoundError: If no xlsx file is found.
        ValueError: If expected columns are missing.
    """
    global _data_cache
    if _data_cache:
        return _data_cache

    if xlsx_path is None:
        xlsx_files = list(DATA_RAW_DIR.glob("*.xlsx"))
        if not xlsx_files:
            raise FileNotFoundError(f"No .xlsx files found in {DATA_RAW_DIR}")
        xlsx_path = xlsx_files[0]

    xlsx_path = Path(xlsx_path)
    logger.info("Loading data from %s", xlsx_path)

    # Read sheets
    df_metrics = pd.read_excel(xlsx_path, sheet_name="RAW_INPUT_METRICS")
    df_orders = pd.read_excel(xlsx_path, sheet_name="RAW_ORDERS")
    df_summary = pd.read_excel(xlsx_path, sheet_name="RAW_SUMMARY")

    # Validate columns
    _validate_columns(df_metrics, EXPECTED_COLS_METRICS, "RAW_INPUT_METRICS")
    _validate_columns(df_orders, EXPECTED_COLS_ORDERS, "RAW_ORDERS")

    # Basic validation
    _validate_data(df_metrics, df_orders)

    _data_cache = {
        "metrics": df_metrics,
        "orders": df_orders,
        "summary": df_summary,
    }

    logger.info(
        "Data loaded: metrics=%d rows, orders=%d rows, summary=%d rows",
        len(df_metrics), len(df_orders), len(df_summary),
    )
    return _data_cache


def _validate_columns(df: pd.DataFrame, expected: list[str], sheet_name: str) -> None:
    """Check that expected columns exist in the DataFrame."""
    missing = set(expected) - set(df.columns)
    if missing:
        raise ValueError(f"Sheet '{sheet_name}' is missing columns: {missing}")


def _validate_data(df_metrics: pd.DataFrame, df_orders: pd.DataFrame) -> None:
    """Run basic data quality checks and log warnings."""
    # Check for nulls in key columns
    for col in ["COUNTRY", "CITY", "ZONE", "METRIC"]:
        nulls = df_metrics[col].isna().sum()
        if nulls > 0:
            logger.warning("df_metrics has %d null values in column '%s'", nulls, col)

    # Check numeric columns are within reasonable ranges
    for col in WEEK_COLUMNS_METRICS:
        if col in df_metrics.columns:
            non_numeric = df_metrics[col].apply(lambda x: not isinstance(x, (int, float)) and pd.notna(x)).sum()
            if non_numeric > 0:
                logger.warning("df_metrics column '%s' has %d non-numeric values", col, non_numeric)


def export_to_csv(output_dir: str | Path | None = None) -> None:
    """Export loaded DataFrames to CSV files in the processed directory.

    Args:
        output_dir: Output directory. Defaults to data/processed/.
    """
    if not _data_cache:
        raise RuntimeError("No data loaded. Call load_raw_data() first.")

    output_dir = Path(output_dir) if output_dir else DATA_PROCESSED_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    for name, df in _data_cache.items():
        path = output_dir / f"{name}.csv"
        df.to_csv(path, index=False)
        logger.info("Exported %s → %s (%d rows)", name, path, len(df))


def get_data_summary() -> str:
    """Generate a text summary of the loaded dataset for LLM context.

    Returns:
        Formatted string with dataset statistics.
    """
    if not _data_cache:
        return "No data loaded yet."

    df_m = _data_cache["metrics"]
    df_o = _data_cache["orders"]

    countries = sorted(df_m["COUNTRY"].unique())
    cities = sorted(df_m["CITY"].unique())
    zones = sorted(df_m["ZONE"].unique())
    metrics = sorted(df_m["METRIC"].unique())

    lines = [
        "=== Rappi Operational Data Summary ===",
        f"Metrics sheet: {len(df_m):,} rows",
        f"Orders sheet:  {len(df_o):,} rows",
        "",
        f"Countries ({len(countries)}): {', '.join(countries)}",
        f"Cities ({len(cities)}): {', '.join(cities[:20])}{'...' if len(cities) > 20 else ''}",
        f"Zones: {len(zones)}",
        f"Metrics ({len(metrics)}):",
    ]

    for m in metrics:
        subset = df_m[df_m["METRIC"] == m]
        latest_col = WEEK_COLUMNS_METRICS[-1]  # L0W_ROLL
        vals = pd.to_numeric(subset[latest_col], errors="coerce").dropna()
        if len(vals) > 0:
            lines.append(
                f"  - {m}: min={vals.min():.4f}, max={vals.max():.4f}, "
                f"mean={vals.mean():.4f}, median={vals.median():.4f}"
            )
        else:
            lines.append(f"  - {m}: no numeric data available")

    lines.append("")
    lines.append(f"Time window: 9 weeks (L8W to L0W, where L0W is the most recent)")

    return "\n".join(lines)
