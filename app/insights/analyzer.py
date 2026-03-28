"""
Insight Analyzer - Automatic detection of anomalies, trends, benchmarking,
correlations, and opportunities across Rappi operational data.
"""

import logging

import numpy as np
import pandas as pd

from app.config import WEEK_COLUMNS_METRICS, WEEK_COLUMNS_ORDERS

logger = logging.getLogger(__name__)

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

# Metrics where higher value is WORSE (inverted polarity)
_INVERTED_METRICS = {"Restaurants Markdowns / GMV"}


def _is_worse(metric: str, old_val: float, new_val: float) -> bool:
    """Return True if the change from old_val to new_val represents deterioration."""
    if metric in _INVERTED_METRICS:
        return new_val > old_val  # higher markdowns = worse
    return new_val < old_val  # for most metrics, lower = worse


def _pct_change(old: float, new: float) -> float:
    if old == 0:
        return 0.0
    return ((new - old) / abs(old)) * 100


class InsightsAnalyzer:
    """Analyzes DataFrames to detect insights across 5 categories.

    Args:
        df_metrics: RAW_INPUT_METRICS DataFrame.
        df_orders: RAW_ORDERS DataFrame.
    """

    def __init__(self, df_metrics: pd.DataFrame, df_orders: pd.DataFrame):
        self.metrics = df_metrics.copy()
        self.orders = df_orders.copy()
        # Ensure numeric week columns
        for col in WEEK_COLUMNS_METRICS:
            if col in self.metrics.columns:
                self.metrics[col] = pd.to_numeric(self.metrics[col], errors="coerce")
        for col in WEEK_COLUMNS_ORDERS:
            if col in self.orders.columns:
                self.orders[col] = pd.to_numeric(self.orders[col], errors="coerce")

        self._metric_names = sorted(self.metrics["METRIC"].unique().tolist())

    def analyze_all(self) -> list[dict]:
        """Run all analysis categories and return insights sorted by severity."""
        logger.info("Starting full insights analysis...")
        insights = []
        insights.extend(self._detect_anomalies())
        insights.extend(self._detect_trends())
        insights.extend(self._detect_benchmarking())
        insights.extend(self._detect_correlations())
        insights.extend(self._detect_opportunities())
        insights.sort(key=lambda x: SEVERITY_ORDER.get(x.get("severity", "low"), 3))
        logger.info("Analysis complete: %d insights found.", len(insights))
        return insights

    # ------------------------------------------------------------------
    # a) ANOMALIAS
    # ------------------------------------------------------------------
    def _detect_anomalies(self) -> list[dict]:
        insights = []
        curr, prev = "L0W_ROLL", "L1W_ROLL"

        for metric_name in self._metric_names:
            df = self.metrics[self.metrics["METRIC"] == metric_name].copy()
            df = df.dropna(subset=[curr, prev])
            df = df[df[prev] != 0]
            df["_pct"] = _pct_change(0, 0)  # placeholder
            df["_pct"] = df.apply(lambda r: _pct_change(r[prev], r[curr]), axis=1)
            anomalies = df[df["_pct"].abs() > 10]

            for _, row in anomalies.iterrows():
                pct = row["_pct"]
                worse = _is_worse(metric_name, row[prev], row[curr])
                severity = "critical" if abs(pct) > 20 else "high"
                direction = "deterioro" if worse else "mejora"

                insights.append({
                    "category": "anomaly",
                    "severity": severity,
                    "title": f"{direction.capitalize()} de {pct:+.1f}% en {metric_name} - {row['ZONE']}",
                    "description": (
                        f"La zona {row['ZONE']} ({row['COUNTRY']}, {row['CITY']}) "
                        f"tuvo un cambio de {pct:+.1f}% en {metric_name} "
                        f"(de {row[prev]:.4f} a {row[curr]:.4f}). "
                        f"Esto representa un {direction} {'significativo' if severity == 'critical' else 'notable'}."
                    ),
                    "zones": [row["ZONE"]],
                    "metrics": [metric_name],
                    "data": {
                        "previous": round(row[prev], 4),
                        "current": round(row[curr], 4),
                        "pct_change": round(pct, 2),
                        "direction": direction,
                        "country": row["COUNTRY"],
                    },
                    "recommendation": (
                        f"Investigar la causa del {direction} en {row['ZONE']} y "
                        f"{'tomar acciones correctivas' if worse else 'replicar las buenas practicas'}."
                    ),
                    "chart_data": None,
                })

        # Order anomalies
        oc, op = "L0W", "L1W"
        odf = self.orders.dropna(subset=[oc, op])
        odf = odf[odf[op] > 0]
        odf = odf.copy()
        odf["_pct"] = odf.apply(lambda r: _pct_change(r[op], r[oc]), axis=1)
        order_anom = odf[odf["_pct"].abs() > 10]

        for _, row in order_anom.iterrows():
            pct = row["_pct"]
            severity = "critical" if abs(pct) > 20 else "high"
            direction = "caida" if pct < 0 else "crecimiento"
            insights.append({
                "category": "anomaly",
                "severity": severity,
                "title": f"{direction.capitalize()} de ordenes {pct:+.1f}% - {row['ZONE']}",
                "description": (
                    f"La zona {row['ZONE']} ({row['COUNTRY']}, {row['CITY']}) "
                    f"tuvo un cambio de {pct:+.1f}% en ordenes "
                    f"(de {row[op]:,.0f} a {row[oc]:,.0f})."
                ),
                "zones": [row["ZONE"]],
                "metrics": ["Orders"],
                "data": {
                    "previous": int(row[op]),
                    "current": int(row[oc]),
                    "pct_change": round(pct, 2),
                    "direction": direction,
                },
                "recommendation": f"Revisar operacion de {row['ZONE']} para entender el {direction} de ordenes.",
                "chart_data": None,
            })

        # Cap to top 50 most severe anomalies to keep report manageable
        insights.sort(key=lambda x: abs(x["data"].get("pct_change", 0)), reverse=True)
        return insights[:50]

    # ------------------------------------------------------------------
    # b) TENDENCIAS PREOCUPANTES
    # ------------------------------------------------------------------
    def _detect_trends(self) -> list[dict]:
        insights = []
        week_cols = WEEK_COLUMNS_METRICS  # L8W_ROLL .. L0W_ROLL chronological

        for metric_name in self._metric_names:
            df = self.metrics[self.metrics["METRIC"] == metric_name].copy()
            df = df.dropna(subset=week_cols)

            for _, row in df.iterrows():
                values = [row[w] for w in week_cols]
                # Count consecutive deterioration from the most recent week backwards
                consec = 0
                for i in range(len(values) - 1, 0, -1):
                    if _is_worse(metric_name, values[i - 1], values[i]):
                        consec += 1
                    else:
                        break

                if consec >= 3:
                    start_idx = len(values) - 1 - consec
                    start_val = values[start_idx]
                    end_val = values[-1]
                    pct = _pct_change(start_val, end_val)

                    severity = "critical" if consec >= 5 else "high" if consec >= 4 else "medium"

                    insights.append({
                        "category": "trend",
                        "severity": severity,
                        "title": f"{metric_name} en deterioro {consec} semanas - {row['ZONE']}",
                        "description": (
                            f"La zona {row['ZONE']} ({row['COUNTRY']}) muestra deterioro "
                            f"consecutivo en {metric_name} durante {consec} semanas "
                            f"(de {start_val:.4f} a {end_val:.4f}, {pct:+.1f}%)."
                        ),
                        "zones": [row["ZONE"]],
                        "metrics": [metric_name],
                        "data": {
                            "consecutive_weeks": consec,
                            "start_value": round(start_val, 4),
                            "end_value": round(end_val, 4),
                            "pct_change": round(pct, 2),
                            "country": row["COUNTRY"],
                        },
                        "recommendation": (
                            f"Priorizar revision de {row['ZONE']}: {consec} semanas de "
                            f"deterioro continuo en {metric_name} requiere intervencion."
                        ),
                        "chart_data": {
                            "type": "line",
                            "x": week_cols,
                            "y": [round(v, 4) if pd.notna(v) else None for v in values],
                            "labels": {
                                "title": f"{metric_name} - {row['ZONE']}",
                                "x": "Semana", "y": metric_name,
                            },
                        },
                    })

        insights.sort(key=lambda x: x["data"].get("consecutive_weeks", 0), reverse=True)
        return insights[:40]

    # ------------------------------------------------------------------
    # c) BENCHMARKING
    # ------------------------------------------------------------------
    def _detect_benchmarking(self) -> list[dict]:
        insights = []
        curr = "L0W_ROLL"

        for metric_name in self._metric_names:
            df = self.metrics[self.metrics["METRIC"] == metric_name].copy()
            df = df.dropna(subset=[curr])
            df["_group"] = df["COUNTRY"] + " - " + df["ZONE_TYPE"].fillna("Unknown")

            for group_name, group_df in df.groupby("_group"):
                if len(group_df) < 5:
                    continue
                mean = group_df[curr].mean()
                std = group_df[curr].std()
                if std == 0:
                    continue

                threshold_low = mean - 1.5 * std
                threshold_high = mean + 1.5 * std

                # Underperformers
                if metric_name in _INVERTED_METRICS:
                    under = group_df[group_df[curr] > threshold_high]
                else:
                    under = group_df[group_df[curr] < threshold_low]

                for _, row in under.iterrows():
                    diff = row[curr] - mean
                    z_score = diff / std
                    insights.append({
                        "category": "benchmark",
                        "severity": "high" if abs(z_score) > 2 else "medium",
                        "title": f"{row['ZONE']} underperforming en {metric_name} vs peers",
                        "description": (
                            f"La zona {row['ZONE']} ({row['COUNTRY']}, {row['ZONE_TYPE']}) "
                            f"tiene {metric_name} = {row[curr]:.4f}, "
                            f"mientras el promedio de su grupo ({group_name}) es {mean:.4f} "
                            f"(desviacion: {z_score:.1f} std)."
                        ),
                        "zones": [row["ZONE"]],
                        "metrics": [metric_name],
                        "data": {
                            "zone_value": round(row[curr], 4),
                            "group_mean": round(mean, 4),
                            "group_std": round(std, 4),
                            "z_score": round(z_score, 2),
                            "group": group_name,
                        },
                        "recommendation": (
                            f"Revisar por que {row['ZONE']} esta por debajo de zonas similares "
                            f"en {group_name} para {metric_name}."
                        ),
                        "chart_data": None,
                    })

                # Overperformers (cases of success) - just a few
                if metric_name in _INVERTED_METRICS:
                    over = group_df[group_df[curr] < threshold_low]
                else:
                    over = group_df[group_df[curr] > threshold_high]

                for _, row in over.head(3).iterrows():
                    z_score = (row[curr] - mean) / std
                    insights.append({
                        "category": "benchmark",
                        "severity": "low",
                        "title": f"{row['ZONE']} overperforming en {metric_name} vs peers",
                        "description": (
                            f"La zona {row['ZONE']} destaca con {metric_name} = {row[curr]:.4f} "
                            f"vs promedio de grupo {mean:.4f} en {group_name}."
                        ),
                        "zones": [row["ZONE"]],
                        "metrics": [metric_name],
                        "data": {
                            "zone_value": round(row[curr], 4),
                            "group_mean": round(mean, 4),
                            "z_score": round(z_score, 2),
                            "group": group_name,
                            "overperforming": True,
                        },
                        "recommendation": f"Estudiar las practicas de {row['ZONE']} como caso de exito.",
                        "chart_data": None,
                    })

        # Keep top underperformers and a few overperformers
        under = [i for i in insights if not i["data"].get("overperforming")]
        over = [i for i in insights if i["data"].get("overperforming")]
        under.sort(key=lambda x: x["data"].get("z_score", 0))
        return under[:30] + over[:10]

    # ------------------------------------------------------------------
    # d) CORRELACIONES
    # ------------------------------------------------------------------
    def _detect_correlations(self) -> list[dict]:
        insights = []
        curr = "L0W_ROLL"

        # Pivot: rows=ZONE, columns=METRIC, values=L0W_ROLL
        pivot = self.metrics.pivot_table(index="ZONE", columns="METRIC", values=curr, aggfunc="first")
        pivot = pivot.dropna(axis=1, thresh=int(len(pivot) * 0.5))  # drop metrics with too many NaN

        if pivot.shape[1] < 2:
            return insights

        corr_matrix = pivot.corr()

        seen = set()
        for m_a in corr_matrix.columns:
            for m_b in corr_matrix.columns:
                if m_a >= m_b:
                    continue
                pair = (m_a, m_b)
                if pair in seen:
                    continue
                seen.add(pair)

                r = corr_matrix.loc[m_a, m_b]
                if pd.isna(r) or abs(r) < 0.5:
                    continue

                direction = "positiva" if r > 0 else "negativa"
                strength = "fuerte" if abs(r) >= 0.7 else "moderada"

                if r > 0:
                    desc = f"Las zonas con alto {m_a} tienden a tener alto {m_b}"
                else:
                    desc = f"Las zonas con alto {m_a} tienden a tener bajo {m_b}"

                insights.append({
                    "category": "correlation",
                    "severity": "medium" if abs(r) >= 0.7 else "low",
                    "title": f"Correlacion {strength} entre {m_a} y {m_b}",
                    "description": f"{desc} (r={r:.2f}). Correlacion {strength} {direction}.",
                    "zones": [],
                    "metrics": [m_a, m_b],
                    "data": {
                        "correlation": round(r, 4),
                        "strength": strength,
                        "direction": direction,
                    },
                    "recommendation": (
                        f"Considerar la relacion entre {m_a} y {m_b} al disenar intervenciones: "
                        f"mejorar una puede impactar la otra."
                    ),
                    "chart_data": {
                        "type": "scatter",
                        "x": pivot[m_a].dropna().tolist()[:100],
                        "y": pivot[m_b].dropna().tolist()[:100],
                        "labels": {"title": f"{m_a} vs {m_b} (r={r:.2f})", "x": m_a, "y": m_b},
                    },
                })

        insights.sort(key=lambda x: abs(x["data"].get("correlation", 0)), reverse=True)
        return insights[:15]

    # ------------------------------------------------------------------
    # e) OPORTUNIDADES
    # ------------------------------------------------------------------
    def _detect_opportunities(self) -> list[dict]:
        insights = []
        curr = "L0W_ROLL"
        week_cols = WEEK_COLUMNS_METRICS

        # 1. Zones with high orders but low Perfect Orders
        if "Perfect Orders" in self._metric_names:
            po = self.metrics[self.metrics["METRIC"] == "Perfect Orders"].copy()
            po = po.dropna(subset=[curr])
            po_median = po[curr].median()

            merged = pd.merge(
                po[["ZONE", "COUNTRY", curr]].rename(columns={curr: "perfect_orders"}),
                self.orders[["ZONE", "L0W"]].rename(columns={"L0W": "orders"}),
                on="ZONE",
            )
            merged = merged.dropna()
            orders_p75 = merged["orders"].quantile(0.75)

            high_vol_low_quality = merged[
                (merged["orders"] > orders_p75) & (merged["perfect_orders"] < po_median)
            ]

            for _, row in high_vol_low_quality.head(10).iterrows():
                insights.append({
                    "category": "opportunity",
                    "severity": "high",
                    "title": f"Alto volumen + bajo Perfect Orders en {row['ZONE']}",
                    "description": (
                        f"{row['ZONE']} ({row['COUNTRY']}) tiene {row['orders']:,.0f} ordenes "
                        f"(top 25%) pero Perfect Orders de solo {row['perfect_orders']:.4f} "
                        f"(por debajo de la mediana {po_median:.4f}). "
                        f"Mejorar calidad aqui tendria alto impacto."
                    ),
                    "zones": [row["ZONE"]],
                    "metrics": ["Perfect Orders", "Orders"],
                    "data": {
                        "orders": int(row["orders"]),
                        "perfect_orders": round(row["perfect_orders"], 4),
                        "median_po": round(po_median, 4),
                    },
                    "recommendation": (
                        f"Priorizar mejoras de calidad de servicio en {row['ZONE']}: "
                        f"alto volumen amplifica el impacto de cada orden defectuosa."
                    ),
                    "chart_data": None,
                })

        # 2. Countries below global average
        for metric_name in self._metric_names:
            df = self.metrics[self.metrics["METRIC"] == metric_name].copy()
            df = df.dropna(subset=[curr])
            global_mean = df[curr].mean()
            country_means = df.groupby("COUNTRY")[curr].mean()

            for country, c_mean in country_means.items():
                diff_pct = _pct_change(global_mean, c_mean)
                if metric_name in _INVERTED_METRICS:
                    is_below = c_mean > global_mean * 1.15  # 15% worse
                else:
                    is_below = c_mean < global_mean * 0.85  # 15% below

                if is_below:
                    insights.append({
                        "category": "opportunity",
                        "severity": "medium",
                        "title": f"{country} por debajo del promedio global en {metric_name}",
                        "description": (
                            f"El pais {country} tiene un promedio de {c_mean:.4f} en {metric_name}, "
                            f"{abs(diff_pct):.1f}% por debajo del promedio global ({global_mean:.4f})."
                        ),
                        "zones": [],
                        "metrics": [metric_name],
                        "data": {
                            "country": country,
                            "country_mean": round(c_mean, 4),
                            "global_mean": round(global_mean, 4),
                            "diff_pct": round(diff_pct, 2),
                        },
                        "recommendation": (
                            f"Revisar estrategia de {metric_name} en {country}: "
                            f"hay margen de mejora respecto al benchmark global."
                        ),
                        "chart_data": None,
                    })

        # 3. Zones improving 3+ weeks (positive momentum)
        for metric_name in self._metric_names[:5]:  # limit to top 5 metrics for performance
            df = self.metrics[self.metrics["METRIC"] == metric_name].copy()
            df = df.dropna(subset=week_cols)

            for _, row in df.iterrows():
                values = [row[w] for w in week_cols]
                consec = 0
                for i in range(len(values) - 1, 0, -1):
                    if not _is_worse(metric_name, values[i - 1], values[i]):
                        consec += 1
                    else:
                        break

                if consec >= 3:
                    pct = _pct_change(values[len(values) - 1 - consec], values[-1])
                    insights.append({
                        "category": "opportunity",
                        "severity": "low",
                        "title": f"{row['ZONE']} mejorando {consec} semanas en {metric_name}",
                        "description": (
                            f"{row['ZONE']} ({row['COUNTRY']}) muestra mejora continua en "
                            f"{metric_name} durante {consec} semanas ({pct:+.1f}%)."
                        ),
                        "zones": [row["ZONE"]],
                        "metrics": [metric_name],
                        "data": {
                            "consecutive_weeks": consec,
                            "pct_change": round(pct, 2),
                            "country": row["COUNTRY"],
                        },
                        "recommendation": f"Caso de exito: investigar que esta funcionando en {row['ZONE']}.",
                        "chart_data": None,
                    })

        return insights[:30]
