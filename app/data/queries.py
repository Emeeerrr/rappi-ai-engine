"""
Data Queries - DataQueryEngine for operational DataFrames.

Provides filtering, ranking, comparisons, trends, aggregations,
multi-variable analysis, orders analysis, and utility methods.
All results include a Spanish-language summary for direct LLM use.
"""

import logging
import operator
from difflib import get_close_matches

import numpy as np
import pandas as pd

from app.config import WEEK_COLUMNS_METRICS, WEEK_COLUMNS_ORDERS
from app.data.metrics import METRICS

logger = logging.getLogger(__name__)

OPERATOR_MAP = {
    ">": operator.gt,
    "<": operator.lt,
    ">=": operator.ge,
    "<=": operator.le,
    "==": operator.eq,
}

# Week label mappings for readable summaries
_WEEK_LABEL = {
    "L0W_ROLL": "semana actual", "L1W_ROLL": "hace 1 semana",
    "L2W_ROLL": "hace 2 semanas", "L3W_ROLL": "hace 3 semanas",
    "L4W_ROLL": "hace 4 semanas", "L5W_ROLL": "hace 5 semanas",
    "L6W_ROLL": "hace 6 semanas", "L7W_ROLL": "hace 7 semanas",
    "L8W_ROLL": "hace 8 semanas",
    "L0W": "semana actual", "L1W": "hace 1 semana",
    "L2W": "hace 2 semanas", "L3W": "hace 3 semanas",
    "L4W": "hace 4 semanas", "L5W": "hace 5 semanas",
    "L6W": "hace 6 semanas", "L7W": "hace 7 semanas",
    "L8W": "hace 8 semanas",
}


def _ok(data, summary: str, chart_data=None) -> dict:
    return {"success": True, "data": data, "summary": summary, "chart_data": chart_data}


def _err(message: str) -> dict:
    return {"success": False, "data": None, "summary": message, "chart_data": None}


def _fmt(value) -> str:
    """Format a numeric value for display."""
    if pd.isna(value):
        return "N/A"
    if isinstance(value, float):
        if abs(value) < 1:
            return f"{value:.4f}"
        return f"{value:,.2f}"
    return str(value)


class DataQueryEngine:
    """Query engine over Rappi operational DataFrames.

    Args:
        df_metrics: RAW_INPUT_METRICS DataFrame.
        df_orders: RAW_ORDERS DataFrame.
    """

    def __init__(self, df_metrics: pd.DataFrame, df_orders: pd.DataFrame):
        self.metrics = df_metrics.copy()
        self.orders = df_orders.copy()

        # Precompute lowercase lookup columns for case-insensitive matching
        for col in ["COUNTRY", "CITY", "ZONE", "METRIC"]:
            if col in self.metrics.columns:
                self.metrics[f"_{col}_lower"] = self.metrics[col].astype(str).str.lower().str.strip()
            if col in self.orders.columns:
                self.orders[f"_{col}_lower"] = self.orders[col].astype(str).str.lower().str.strip()
        if "ZONE_TYPE" in self.metrics.columns:
            self.metrics["_ZONE_TYPE_lower"] = self.metrics["ZONE_TYPE"].astype(str).str.lower().str.strip()
        if "ZONE_PRIORITIZATION" in self.metrics.columns:
            self.metrics["_ZONE_PRIORITIZATION_lower"] = self.metrics["ZONE_PRIORITIZATION"].astype(str).str.lower().str.strip()

        # Ensure week columns are numeric
        for col in WEEK_COLUMNS_METRICS:
            if col in self.metrics.columns:
                self.metrics[col] = pd.to_numeric(self.metrics[col], errors="coerce")
        for col in WEEK_COLUMNS_ORDERS:
            if col in self.orders.columns:
                self.orders[col] = pd.to_numeric(self.orders[col], errors="coerce")

        # Available metric names (original casing)
        self._metric_names = sorted(self.metrics["METRIC"].unique().tolist())
        self._zone_names = sorted(self.metrics["ZONE"].unique().tolist())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_metric(self, metric: str) -> str | None:
        """Resolve a metric name with fuzzy/partial matching. Returns exact name or None."""
        if metric in self._metric_names:
            return metric
        # Case-insensitive exact
        lower = metric.lower().strip()
        for m in self._metric_names:
            if m.lower() == lower:
                return m
        # Partial match (substring)
        for m in self._metric_names:
            if lower in m.lower():
                return m
        # Fuzzy
        matches = get_close_matches(metric, self._metric_names, n=1, cutoff=0.4)
        return matches[0] if matches else None

    def _resolve_zone(self, zone: str) -> str | None:
        """Resolve a zone name with fuzzy matching."""
        if zone in self._zone_names:
            return zone
        lower = zone.lower().strip()
        for z in self._zone_names:
            if z.lower() == lower:
                return z
        for z in self._zone_names:
            if lower in z.lower():
                return z
        matches = get_close_matches(zone, self._zone_names, n=1, cutoff=0.4)
        return matches[0] if matches else None

    def _filter_df(self, df: pd.DataFrame, country=None, city=None,
                   zone=None, zone_type=None, prioritization=None,
                   metric=None) -> pd.DataFrame:
        """Apply case-insensitive filters to a DataFrame."""
        mask = pd.Series(True, index=df.index)
        if country:
            mask &= df["_COUNTRY_lower"] == country.lower().strip()
        if city:
            mask &= df["_CITY_lower"] == city.lower().strip()
        if zone:
            resolved = self._resolve_zone(zone)
            if resolved:
                mask &= df["_ZONE_lower"] == resolved.lower()
            else:
                mask &= False
        if zone_type and "_ZONE_TYPE_lower" in df.columns:
            mask &= df["_ZONE_TYPE_lower"] == zone_type.lower().strip()
        if prioritization and "_ZONE_PRIORITIZATION_lower" in df.columns:
            mask &= df["_ZONE_PRIORITIZATION_lower"] == prioritization.lower().strip()
        if metric:
            resolved = self._resolve_metric(metric)
            if resolved:
                mask &= df["_METRIC_lower"] == resolved.lower()
            else:
                mask &= False
        return df[mask]

    def _week_label(self, week: str) -> str:
        return _WEEK_LABEL.get(week, week)

    # ------------------------------------------------------------------
    # a) FILTRADO Y RANKING
    # ------------------------------------------------------------------

    def top_zones_by_metric(self, metric: str, week: str = "L0W_ROLL", n: int = 5,
                            ascending: bool = False, country=None, city=None,
                            zone_type=None, prioritization=None) -> dict:
        """Top N zonas para una metrica dada."""
        resolved = self._resolve_metric(metric)
        if not resolved:
            return _err(f"No se encontro la metrica '{metric}'. Metricas disponibles: {', '.join(self._metric_names)}")
        if week not in WEEK_COLUMNS_METRICS:
            return _err(f"Columna de semana '{week}' no valida. Opciones: {WEEK_COLUMNS_METRICS}")

        df = self._filter_df(self.metrics, country=country, city=city,
                             zone_type=zone_type, prioritization=prioritization, metric=resolved)
        if df.empty:
            return _err(f"No se encontraron datos para '{resolved}' con los filtros indicados.")

        df_sorted = df.dropna(subset=[week]).sort_values(week, ascending=ascending).head(n)
        result = df_sorted[["ZONE", "COUNTRY", "CITY", week]].copy()
        result.columns = ["Zona", "Pais", "Ciudad", "Valor"]

        direction = "peores" if ascending else "mejores"
        filters_desc = self._describe_filters(country, city, zone_type, prioritization)
        summary_lines = [f"Las {n} {direction} zonas en '{resolved}' ({self._week_label(week)}){filters_desc}:"]
        for _, row in result.iterrows():
            summary_lines.append(f"  - {row['Zona']} ({row['Pais']}, {row['Ciudad']}): {_fmt(row['Valor'])}")

        chart = {
            "type": "bar",
            "x": result["Zona"].tolist(),
            "y": result["Valor"].tolist(),
            "labels": {"title": f"Top {n} {direction} zonas - {resolved}", "x": "Zona", "y": resolved},
        }
        return _ok(result, "\n".join(summary_lines), chart)

    def bottom_zones_by_metric(self, metric: str, week: str = "L0W_ROLL", n: int = 5,
                               country=None, city=None, zone_type=None,
                               prioritization=None) -> dict:
        """Bottom N zonas para una metrica dada."""
        return self.top_zones_by_metric(metric, week, n, ascending=True,
                                        country=country, city=city,
                                        zone_type=zone_type, prioritization=prioritization)

    def filter_zones(self, filters: dict) -> dict:
        """Filtrado generico por combinacion de COUNTRY, CITY, ZONE_TYPE, ZONE_PRIORITIZATION."""
        df = self._filter_df(
            self.metrics,
            country=filters.get("COUNTRY") or filters.get("country"),
            city=filters.get("CITY") or filters.get("city"),
            zone_type=filters.get("ZONE_TYPE") or filters.get("zone_type"),
            prioritization=filters.get("ZONE_PRIORITIZATION") or filters.get("prioritization"),
        )
        if df.empty:
            return _err("No se encontraron zonas con los filtros indicados.")

        zones = sorted(df["ZONE"].unique().tolist())
        parts = [f"{k}={v}" for k, v in filters.items() if v]
        summary = f"Se encontraron {len(zones)} zonas con filtros ({', '.join(parts)})."
        return _ok(zones, summary)

    # ------------------------------------------------------------------
    # b) COMPARACIONES
    # ------------------------------------------------------------------

    def compare_metric_by_group(self, metric: str, group_by: str,
                                week: str = "L0W_ROLL", filters: dict = None) -> dict:
        """Compara promedios de una metrica agrupada por una dimension."""
        resolved = self._resolve_metric(metric)
        if not resolved:
            return _err(f"No se encontro la metrica '{metric}'.")
        valid_groups = ["ZONE_TYPE", "COUNTRY", "CITY", "ZONE_PRIORITIZATION"]
        group_upper = group_by.upper()
        if group_upper not in valid_groups:
            return _err(f"Agrupacion '{group_by}' no valida. Opciones: {valid_groups}")
        if week not in WEEK_COLUMNS_METRICS:
            return _err(f"Columna de semana '{week}' no valida.")

        df = self._filter_df(self.metrics, metric=resolved,
                             country=(filters or {}).get("country"),
                             city=(filters or {}).get("city"),
                             zone_type=(filters or {}).get("zone_type"),
                             prioritization=(filters or {}).get("prioritization"))
        if df.empty:
            return _err(f"No hay datos para '{resolved}' con los filtros indicados.")

        agg = df.groupby(group_upper)[week].agg(["mean", "median", "count"]).reset_index()
        agg.columns = [group_upper, "Promedio", "Mediana", "N_Zonas"]
        agg = agg.sort_values("Promedio", ascending=False)

        summary_lines = [f"Comparacion de '{resolved}' por {group_upper} ({self._week_label(week)}):"]
        for _, row in agg.iterrows():
            summary_lines.append(
                f"  - {row[group_upper]}: promedio={_fmt(row['Promedio'])}, "
                f"mediana={_fmt(row['Mediana'])}, zonas={int(row['N_Zonas'])}"
            )

        chart = {
            "type": "bar",
            "x": agg[group_upper].tolist(),
            "y": agg["Promedio"].tolist(),
            "labels": {"title": f"{resolved} por {group_upper}", "x": group_upper, "y": "Promedio"},
        }
        return _ok(agg, "\n".join(summary_lines), chart)

    def compare_zones(self, zone_list: list[str], metric: str,
                      weeks: list[str] | None = None) -> dict:
        """Compara zonas especificas para una metrica en las semanas indicadas."""
        resolved = self._resolve_metric(metric)
        if not resolved:
            return _err(f"No se encontro la metrica '{metric}'.")

        weeks = weeks or WEEK_COLUMNS_METRICS
        resolved_zones = []
        for z in zone_list:
            rz = self._resolve_zone(z)
            if rz:
                resolved_zones.append(rz)
            else:
                return _err(f"No se encontro la zona '{z}'. Intenta con un nombre similar.")

        df = self._filter_df(self.metrics, metric=resolved)
        df = df[df["ZONE"].isin(resolved_zones)]
        if df.empty:
            return _err(f"No se encontraron datos para las zonas indicadas en '{resolved}'.")

        result = df[["ZONE", *weeks]].copy()
        result = result.set_index("ZONE")

        summary_lines = [f"Comparacion de '{resolved}' entre zonas:"]
        for zone_name in result.index:
            vals = [_fmt(result.loc[zone_name, w]) for w in weeks]
            summary_lines.append(f"  - {zone_name}: {' ->'.join(vals)}")

        chart = {
            "type": "line",
            "x": [self._week_label(w) for w in weeks],
            "y": {str(z): result.loc[z, weeks].tolist() for z in result.index},
            "labels": {"title": f"{resolved} - Comparacion de zonas", "x": "Semana", "y": resolved},
        }
        return _ok(result.reset_index(), "\n".join(summary_lines), chart)

    # ------------------------------------------------------------------
    # c) TENDENCIAS TEMPORALES
    # ------------------------------------------------------------------

    def get_zone_trend(self, zone: str, metric: str, num_weeks: int = 8) -> dict:
        """Serie temporal de una zona para una metrica."""
        resolved_zone = self._resolve_zone(zone)
        if not resolved_zone:
            return _err(f"No se encontro la zona '{zone}'.")
        resolved_metric = self._resolve_metric(metric)
        if not resolved_metric:
            return _err(f"No se encontro la metrica '{metric}'.")

        week_cols = WEEK_COLUMNS_METRICS[-num_weeks:]
        df = self._filter_df(self.metrics, zone=resolved_zone, metric=resolved_metric)
        if df.empty:
            return _err(f"No hay datos de '{resolved_metric}' para '{resolved_zone}'.")

        row = df.iloc[0]
        values = [row[w] for w in week_cols]

        summary_lines = [f"Tendencia de '{resolved_metric}' para '{resolved_zone}' (ultimas {num_weeks} semanas):"]
        for w, v in zip(week_cols, values):
            summary_lines.append(f"  - {self._week_label(w)}: {_fmt(v)}")

        # Trend direction
        valid = [v for v in values if pd.notna(v)]
        if len(valid) >= 2:
            change = valid[-1] - valid[0]
            pct = (change / abs(valid[0]) * 100) if valid[0] != 0 else 0
            direction = "subiendo" if change > 0 else "bajando" if change < 0 else "estable"
            summary_lines.append(f"Tendencia: {direction} ({pct:+.1f}% en el periodo).")

        chart = {
            "type": "line",
            "x": [self._week_label(w) for w in week_cols],
            "y": values,
            "labels": {"title": f"{resolved_metric} - {resolved_zone}", "x": "Semana", "y": resolved_metric},
        }
        return _ok(pd.DataFrame({"Semana": week_cols, "Valor": values}), "\n".join(summary_lines), chart)

    def get_aggregated_trend(self, metric: str, group_by: str = None,
                             group_value: str = None, num_weeks: int = 8) -> dict:
        """Tendencia agregada (promedio) para un grupo."""
        resolved = self._resolve_metric(metric)
        if not resolved:
            return _err(f"No se encontro la metrica '{metric}'.")

        week_cols = WEEK_COLUMNS_METRICS[-num_weeks:]
        df = self._filter_df(self.metrics, metric=resolved)

        group_desc = "global"
        if group_by and group_value:
            col = group_by.upper()
            if col in df.columns:
                lower_col = f"_{col}_lower"
                if lower_col in df.columns:
                    df = df[df[lower_col] == group_value.lower().strip()]
                group_desc = f"{col}={group_value}"

        if df.empty:
            return _err(f"No hay datos para '{resolved}' con agrupacion {group_desc}.")

        means = [df[w].mean() for w in week_cols]

        summary_lines = [f"Tendencia promedio de '{resolved}' ({group_desc}, ultimas {num_weeks} semanas):"]
        for w, v in zip(week_cols, means):
            summary_lines.append(f"  - {self._week_label(w)}: {_fmt(v)}")

        valid = [v for v in means if pd.notna(v)]
        if len(valid) >= 2:
            change = valid[-1] - valid[0]
            pct = (change / abs(valid[0]) * 100) if valid[0] != 0 else 0
            direction = "subiendo" if change > 0 else "bajando" if change < 0 else "estable"
            summary_lines.append(f"Tendencia: {direction} ({pct:+.1f}%).")

        chart = {
            "type": "line",
            "x": [self._week_label(w) for w in week_cols],
            "y": means,
            "labels": {"title": f"{resolved} promedio - {group_desc}", "x": "Semana", "y": resolved},
        }
        return _ok(pd.DataFrame({"Semana": week_cols, "Promedio": means}), "\n".join(summary_lines), chart)

    # ------------------------------------------------------------------
    # d) AGREGACIONES
    # ------------------------------------------------------------------

    def aggregate_metric(self, metric: str, group_by: str, agg_func: str = "mean",
                         filters: dict = None) -> dict:
        """Agrega una metrica por dimension con la funcion indicada."""
        resolved = self._resolve_metric(metric)
        if not resolved:
            return _err(f"No se encontro la metrica '{metric}'.")
        valid_funcs = {"mean", "median", "min", "max", "sum", "std"}
        if agg_func not in valid_funcs:
            return _err(f"Funcion '{agg_func}' no valida. Opciones: {valid_funcs}")
        group_upper = group_by.upper()
        valid_groups = ["COUNTRY", "CITY", "ZONE_TYPE", "ZONE_PRIORITIZATION"]
        if group_upper not in valid_groups:
            return _err(f"Agrupacion '{group_by}' no valida. Opciones: {valid_groups}")

        week = "L0W_ROLL"
        df = self._filter_df(self.metrics, metric=resolved,
                             country=(filters or {}).get("country"),
                             city=(filters or {}).get("city"),
                             zone_type=(filters or {}).get("zone_type"),
                             prioritization=(filters or {}).get("prioritization"))
        if df.empty:
            return _err(f"No hay datos para '{resolved}' con los filtros indicados.")

        agg = df.groupby(group_upper)[week].agg(agg_func).reset_index()
        agg.columns = [group_upper, agg_func]
        agg = agg.sort_values(agg_func, ascending=False)

        summary_lines = [f"{agg_func.capitalize()} de '{resolved}' por {group_upper} ({self._week_label(week)}):"]
        for _, row in agg.iterrows():
            summary_lines.append(f"  - {row[group_upper]}: {_fmt(row[agg_func])}")

        chart = {
            "type": "bar",
            "x": agg[group_upper].tolist(),
            "y": agg[agg_func].tolist(),
            "labels": {"title": f"{agg_func} de {resolved} por {group_upper}", "x": group_upper, "y": agg_func},
        }
        return _ok(agg, "\n".join(summary_lines), chart)

    def get_metric_stats(self, metric: str, filters: dict = None) -> dict:
        """Estadisticas descriptivas de una metrica."""
        resolved = self._resolve_metric(metric)
        if not resolved:
            return _err(f"No se encontro la metrica '{metric}'.")

        week = "L0W_ROLL"
        df = self._filter_df(self.metrics, metric=resolved,
                             country=(filters or {}).get("country"),
                             city=(filters or {}).get("city"),
                             zone_type=(filters or {}).get("zone_type"),
                             prioritization=(filters or {}).get("prioritization"))
        if df.empty:
            return _err(f"No hay datos para '{resolved}' con los filtros indicados.")

        vals = df[week].dropna()
        stats = {
            "mean": vals.mean(),
            "std": vals.std(),
            "min": vals.min(),
            "max": vals.max(),
            "p25": vals.quantile(0.25),
            "p50": vals.quantile(0.50),
            "p75": vals.quantile(0.75),
            "count": len(vals),
        }

        filters_desc = self._describe_filters(
            (filters or {}).get("country"), (filters or {}).get("city"),
            (filters or {}).get("zone_type"), (filters or {}).get("prioritization"),
        )
        summary = (
            f"Estadisticas de '{resolved}' ({self._week_label(week)}){filters_desc}:\n"
            f"  - Promedio: {_fmt(stats['mean'])}\n"
            f"  - Desv. estandar: {_fmt(stats['std'])}\n"
            f"  - Min: {_fmt(stats['min'])}, Max: {_fmt(stats['max'])}\n"
            f"  - Percentiles: P25={_fmt(stats['p25'])}, P50={_fmt(stats['p50'])}, P75={_fmt(stats['p75'])}\n"
            f"  - Total de zonas: {stats['count']}"
        )
        return _ok(stats, summary)

    # ------------------------------------------------------------------
    # e) ANALISIS MULTIVARIABLE
    # ------------------------------------------------------------------

    def multi_metric_filter(self, conditions: list[dict]) -> dict:
        """Filtra zonas que cumplan multiples condiciones simultaneamente.

        Cada condicion: {"metric": str, "operator": ">"|"<"|">="|"<="|"==",
                         "value": float, "week": "L0W_ROLL"}
        """
        if not conditions:
            return _err("Se requiere al menos una condicion.")

        # Start with all zones
        valid_zones = set(self.metrics["ZONE"].unique())
        cond_descriptions = []

        for cond in conditions:
            raw_metric = cond.get("metric", "")
            resolved = self._resolve_metric(raw_metric)
            if not resolved:
                return _err(f"No se encontro la metrica '{raw_metric}'.")
            op_str = cond.get("operator", ">")
            if op_str not in OPERATOR_MAP:
                return _err(f"Operador '{op_str}' no valido. Opciones: {list(OPERATOR_MAP.keys())}")
            value = float(cond.get("value", 0))
            week = cond.get("week", "L0W_ROLL")

            df = self._filter_df(self.metrics, metric=resolved)
            op_func = OPERATOR_MAP[op_str]
            matching = df[op_func(df[week], value)]
            valid_zones &= set(matching["ZONE"].unique())
            cond_descriptions.append(f"{resolved} {op_str} {value}")

        zones = sorted(valid_zones)
        cond_text = " Y ".join(cond_descriptions)
        summary = f"Se encontraron {len(zones)} zonas que cumplen: {cond_text}."
        if zones:
            shown = zones[:10]
            summary += "\n  Ejemplos: " + ", ".join(shown)
            if len(zones) > 10:
                summary += f"... y {len(zones) - 10} mas."

        return _ok(zones, summary)

    def correlate_metrics(self, metric_a: str, metric_b: str,
                          week: str = "L0W_ROLL", filters: dict = None) -> dict:
        """Correlacion entre dos metricas."""
        ra = self._resolve_metric(metric_a)
        rb = self._resolve_metric(metric_b)
        if not ra:
            return _err(f"No se encontro la metrica '{metric_a}'.")
        if not rb:
            return _err(f"No se encontro la metrica '{metric_b}'.")

        df_a = self._filter_df(self.metrics, metric=ra,
                               country=(filters or {}).get("country"),
                               city=(filters or {}).get("city"))
        df_b = self._filter_df(self.metrics, metric=rb,
                               country=(filters or {}).get("country"),
                               city=(filters or {}).get("city"))

        merged = pd.merge(
            df_a[["ZONE", week]].rename(columns={week: ra}),
            df_b[["ZONE", week]].rename(columns={week: rb}),
            on="ZONE",
        ).dropna()

        if len(merged) < 3:
            return _err("No hay suficientes datos para calcular la correlacion.")

        corr = merged[ra].corr(merged[rb])

        if abs(corr) >= 0.7:
            strength = "fuerte"
        elif abs(corr) >= 0.4:
            strength = "moderada"
        else:
            strength = "debil"
        direction = "positiva" if corr > 0 else "negativa"

        summary = (
            f"Correlacion entre '{ra}' y '{rb}' ({self._week_label(week)}): "
            f"{corr:.4f} — correlacion {strength} {direction} (basada en {len(merged)} zonas)."
        )

        chart = {
            "type": "scatter",
            "x": merged[ra].tolist(),
            "y": merged[rb].tolist(),
            "labels": {"title": f"Correlacion: {ra} vs {rb}", "x": ra, "y": rb},
        }
        return _ok(merged, summary, chart)

    # ------------------------------------------------------------------
    # f) ORDENES
    # ------------------------------------------------------------------

    def get_orders_trend(self, zone: str = None, country: str = None,
                         city: str = None) -> dict:
        """Serie temporal de ordenes con filtros opcionales."""
        df = self.orders.copy()
        if country:
            df = df[df["_COUNTRY_lower"] == country.lower().strip()]
        if city:
            df = df[df["_CITY_lower"] == city.lower().strip()]
        if zone:
            rz = self._resolve_zone(zone)
            if rz:
                df = df[df["_ZONE_lower"] == rz.lower()]
            else:
                return _err(f"No se encontro la zona '{zone}'.")

        if df.empty:
            return _err("No se encontraron datos de ordenes con los filtros indicados.")

        week_cols = WEEK_COLUMNS_ORDERS
        totals = [df[w].sum() for w in week_cols]

        filter_parts = []
        if zone:
            filter_parts.append(f"zona={zone}")
        if country:
            filter_parts.append(f"pais={country}")
        if city:
            filter_parts.append(f"ciudad={city}")
        scope = f" ({', '.join(filter_parts)})" if filter_parts else " (global)"

        summary_lines = [f"Tendencia de ordenes{scope}:"]
        for w, t in zip(week_cols, totals):
            summary_lines.append(f"  - {self._week_label(w)}: {t:,.0f}")

        chart = {
            "type": "line",
            "x": [self._week_label(w) for w in week_cols],
            "y": totals,
            "labels": {"title": f"Ordenes{scope}", "x": "Semana", "y": "Ordenes"},
        }
        return _ok(pd.DataFrame({"Semana": week_cols, "Ordenes": totals}), "\n".join(summary_lines), chart)

    def top_zones_by_orders(self, n: int = 10, week: str = "L0W") -> dict:
        """Top zonas por volumen de ordenes."""
        if week not in WEEK_COLUMNS_ORDERS:
            return _err(f"Columna '{week}' no valida. Opciones: {WEEK_COLUMNS_ORDERS}")

        df = self.orders.dropna(subset=[week]).sort_values(week, ascending=False).head(n)
        result = df[["ZONE", "COUNTRY", "CITY", week]].copy()
        result.columns = ["Zona", "Pais", "Ciudad", "Ordenes"]

        summary_lines = [f"Top {n} zonas por volumen de ordenes ({self._week_label(week)}):"]
        for _, row in result.iterrows():
            summary_lines.append(f"  - {row['Zona']} ({row['Pais']}, {row['Ciudad']}): {row['Ordenes']:,.0f}")

        chart = {
            "type": "bar",
            "x": result["Zona"].tolist(),
            "y": result["Ordenes"].tolist(),
            "labels": {"title": f"Top {n} zonas por ordenes", "x": "Zona", "y": "Ordenes"},
        }
        return _ok(result, "\n".join(summary_lines), chart)

    def orders_growth(self, num_weeks: int = 5, n: int = 10) -> dict:
        """Zonas con mayor crecimiento en ordenes (% cambio)."""
        cols = WEEK_COLUMNS_ORDERS[-num_weeks:]
        if len(cols) < 2:
            return _err("Se necesitan al menos 2 semanas para calcular crecimiento.")

        first_col, last_col = cols[0], cols[-1]
        df = self.orders.copy()
        df = df.dropna(subset=[first_col, last_col])
        df = df[df[first_col] > 0]  # Avoid division by zero

        df["_growth"] = ((df[last_col] - df[first_col]) / df[first_col]) * 100
        top = df.sort_values("_growth", ascending=False).head(n)
        result = top[["ZONE", "COUNTRY", "CITY", first_col, last_col, "_growth"]].copy()
        result.columns = ["Zona", "Pais", "Ciudad", f"Ordenes_{first_col}", f"Ordenes_{last_col}", "Crecimiento_%"]

        summary_lines = [f"Top {n} zonas con mayor crecimiento en ordenes ({self._week_label(first_col)} ->{self._week_label(last_col)}):"]
        for _, row in result.iterrows():
            summary_lines.append(
                f"  - {row['Zona']} ({row['Pais']}): {row[f'Ordenes_{first_col}']:,.0f} ->"
                f"{row[f'Ordenes_{last_col}']:,.0f} ({row['Crecimiento_%']:+.1f}%)"
            )

        chart = {
            "type": "bar",
            "x": result["Zona"].tolist(),
            "y": result["Crecimiento_%"].tolist(),
            "labels": {"title": "Crecimiento de ordenes (%)", "x": "Zona", "y": "% Crecimiento"},
        }
        return _ok(result, "\n".join(summary_lines), chart)

    # ------------------------------------------------------------------
    # g) UTILIDADES
    # ------------------------------------------------------------------

    def list_countries(self) -> dict:
        """Lista de paises disponibles."""
        countries = sorted(self.metrics["COUNTRY"].unique().tolist())
        summary = f"Paises disponibles ({len(countries)}): {', '.join(countries)}"
        return _ok(countries, summary)

    def list_cities(self, country: str = None) -> dict:
        """Ciudades disponibles, opcionalmente filtradas por pais."""
        df = self.metrics
        if country:
            df = df[df["_COUNTRY_lower"] == country.lower().strip()]
        cities = sorted(df["CITY"].unique().tolist())
        scope = f" en {country}" if country else ""
        summary = f"Ciudades disponibles{scope} ({len(cities)}): {', '.join(cities)}"
        return _ok(cities, summary)

    def list_zones(self, country: str = None, city: str = None) -> dict:
        """Zonas disponibles, opcionalmente filtradas."""
        df = self.metrics
        if country:
            df = df[df["_COUNTRY_lower"] == country.lower().strip()]
        if city:
            df = df[df["_CITY_lower"] == city.lower().strip()]
        zones = sorted(df["ZONE"].unique().tolist())
        parts = []
        if country:
            parts.append(country)
        if city:
            parts.append(city)
        scope = f" en {', '.join(parts)}" if parts else ""
        summary = f"Zonas disponibles{scope}: {len(zones)} zonas."
        if len(zones) <= 20:
            summary += "\n" + ", ".join(zones)
        else:
            summary += f"\nPrimeras 20: {', '.join(zones[:20])}..."
        return _ok(zones, summary)

    def list_metrics(self) -> dict:
        """Lista de metricas disponibles."""
        summary = f"Metricas disponibles ({len(self._metric_names)}):\n"
        for m in self._metric_names:
            info = METRICS.get(m)
            desc = f" — {info['description']}" if info else ""
            summary += f"  - {m}{desc}\n"
        return _ok(self._metric_names, summary.strip())

    def search_zone(self, query: str) -> dict:
        """Busqueda fuzzy de zona por nombre."""
        # Exact match first
        resolved = self._resolve_zone(query)
        if resolved and resolved.lower() == query.lower():
            return _ok(resolved, f"Zona encontrada: {resolved}")

        matches = get_close_matches(query, self._zone_names, n=5, cutoff=0.3)
        if not matches:
            return _err(f"No se encontraron zonas similares a '{query}'.")

        summary = f"Zonas similares a '{query}':\n" + "\n".join(f"  - {m}" for m in matches)
        return _ok(matches, summary)

    def get_week_columns(self, dataset: str = "metrics") -> dict:
        """Columnas de semanas en orden cronologico."""
        if dataset.lower() == "orders":
            cols = list(WEEK_COLUMNS_ORDERS)
            summary = f"Columnas de semanas (ordenes): {' ->'.join(cols)} (L8W=mas vieja, L0W=mas reciente)"
        else:
            cols = list(WEEK_COLUMNS_METRICS)
            summary = f"Columnas de semanas (metricas): {' ->'.join(cols)} (L8W_ROLL=mas vieja, L0W_ROLL=mas reciente)"
        return _ok(cols, summary)

    # ------------------------------------------------------------------
    # Helper for filter descriptions
    # ------------------------------------------------------------------

    def _describe_filters(self, country=None, city=None, zone_type=None, prioritization=None) -> str:
        parts = []
        if country:
            parts.append(f"pais={country}")
        if city:
            parts.append(f"ciudad={city}")
        if zone_type:
            parts.append(f"tipo={zone_type}")
        if prioritization:
            parts.append(f"priorizacion={prioritization}")
        return f" (filtros: {', '.join(parts)})" if parts else ""


# ======================================================================
# Quick test script
# ======================================================================

if __name__ == "__main__":
    import json

    from app.data.loader import get_dataframes

    print("=" * 60)
    print("Cargando datos...")
    df_metrics, df_orders, df_summary = get_dataframes()
    engine = DataQueryEngine(df_metrics, df_orders)
    print(f"Metrics: {len(df_metrics)} rows | Orders: {len(df_orders)} rows")
    print("=" * 60)

    def show(label: str, result: dict):
        print(f"\n{'-' * 60}")
        print(f"[{label}] success={result['success']}")
        print(result["summary"])
        if result.get("chart_data"):
            print(f"  chart_type={result['chart_data']['type']}")
        print()

    # a) Filtrado y Ranking
    show("a1 - Top 5 zonas Perfect Orders",
         engine.top_zones_by_metric("Perfect Orders", n=5))
    show("a2 - Bottom 5 zonas Lead Penetration en MX",
         engine.bottom_zones_by_metric("Lead Penetration", n=5, country="MX"))
    show("a3 - Filtrar zonas",
         engine.filter_zones({"COUNTRY": "CO"}))

    # b) Comparaciones
    show("b1 - Comparar Perfect Orders por ZONE_TYPE",
         engine.compare_metric_by_group("Perfect Orders", "ZONE_TYPE"))
    show("b2 - Comparar zonas especificas",
         engine.compare_zones(
             engine.list_zones()["data"][:3],
             "Perfect Orders",
             ["L2W_ROLL", "L1W_ROLL", "L0W_ROLL"],
         ))

    # c) Tendencias
    first_zone = engine.list_zones()["data"][0]
    show("c1 - Tendencia de zona",
         engine.get_zone_trend(first_zone, "Perfect Orders", num_weeks=5))
    show("c2 - Tendencia agregada por pais",
         engine.get_aggregated_trend("Perfect Orders", group_by="COUNTRY", group_value="MX"))

    # d) Agregaciones
    show("d1 - Promedio Perfect Orders por COUNTRY",
         engine.aggregate_metric("Perfect Orders", "COUNTRY"))
    show("d2 - Stats de Lead Penetration",
         engine.get_metric_stats("Lead Penetration"))

    # e) Multivariable
    show("e1 - Multi-metric filter",
         engine.multi_metric_filter([
             {"metric": "Lead Penetration", "operator": ">", "value": 0.7, "week": "L0W_ROLL"},
             {"metric": "Perfect Orders", "operator": "<", "value": 0.5, "week": "L0W_ROLL"},
         ]))
    show("e2 - Correlacion",
         engine.correlate_metrics("Lead Penetration", "Perfect Orders"))

    # f) Ordenes
    show("f1 - Tendencia ordenes global",
         engine.get_orders_trend())
    show("f2 - Top zonas por ordenes",
         engine.top_zones_by_orders(n=5))
    show("f3 - Crecimiento de ordenes",
         engine.orders_growth(num_weeks=5, n=5))

    # g) Utilidades
    show("g1 - Paises", engine.list_countries())
    show("g2 - Ciudades en MX", engine.list_cities("MX"))
    show("g3 - Metricas", engine.list_metrics())
    show("g4 - Buscar zona (fuzzy)", engine.search_zone("bogta"))
    show("g5 - Columnas semanas", engine.get_week_columns("metrics"))

    print("=" * 60)
    print("Todas las queries ejecutadas correctamente.")
