"""
Competitive Analysis - Cross-platform comparison engine.

Loads competitive scraping data and performs price, fee, delivery time,
promotion, and geographic analyses across Rappi, UberEats, and DiDi Food.
"""

import json
import logging
import re
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def _parse_time(time_str) -> float | None:
    """Parse '25-34 min' into the midpoint in minutes."""
    if not time_str or not isinstance(time_str, str):
        return None
    nums = re.findall(r"\d+", time_str)
    if not nums:
        return None
    vals = [int(n) for n in nums]
    return sum(vals) / len(vals)


class CompetitiveAnalyzer:
    """Analyzes competitive data across delivery platforms.

    Args:
        data_path: Path to the directory containing competitive_data.json.
              Or a list of dicts (raw data) directly.
    """

    def __init__(self, data_path: str | list):
        if isinstance(data_path, list):
            raw = data_path
        else:
            json_path = Path(data_path) / "competitive_data.json"
            with open(json_path, encoding="utf-8") as f:
                raw = json.load(f)

        # Flatten to one row per platform+address+product
        rows = []
        for r in raw:
            delivery_time_min = _parse_time(r.get("estimated_delivery_time"))
            for p in r.get("products", []):
                rows.append({
                    "platform": r["platform"],
                    "address_id": r["address_id"],
                    "address_label": r["address_label"],
                    "city": r["city"],
                    "zone_type": r["zone_type"],
                    "product": p["name"],
                    "price": p.get("price"),
                    "available": p.get("available", False),
                    "delivery_fee": r.get("delivery_fee"),
                    "service_fee": r.get("service_fee"),
                    "delivery_time_min": delivery_time_min,
                    "total_big_mac_combo": r.get("total_price_big_mac_combo"),
                    "promotions": r.get("promotions", []),
                    "n_promotions": len(r.get("promotions", [])),
                })

        self.df = pd.DataFrame(rows)
        self.df["price"] = pd.to_numeric(self.df["price"], errors="coerce")
        self.df["delivery_fee"] = pd.to_numeric(self.df["delivery_fee"], errors="coerce")
        self.df["service_fee"] = pd.to_numeric(self.df["service_fee"], errors="coerce")

        # Derived fields
        self.df["total_cost"] = self.df["price"] + self.df["delivery_fee"] + self.df["service_fee"]
        avg_price_per_product = self.df.groupby("product")["price"].transform("mean")
        self.df["price_index"] = self.df["price"] / avg_price_per_product

        # Summary-level (one row per platform+address)
        self.df_summary = self.df.drop_duplicates(subset=["platform", "address_id"])[
            ["platform", "address_id", "address_label", "city", "zone_type",
             "delivery_fee", "service_fee", "delivery_time_min", "total_big_mac_combo", "n_promotions"]
        ].copy()

        self._platforms = sorted(self.df["platform"].unique().tolist())
        logger.info("CompetitiveAnalyzer loaded: %d rows, platforms=%s", len(self.df), self._platforms)

    # ------------------------------------------------------------------
    # b) Price comparison
    # ------------------------------------------------------------------
    def price_comparison(self) -> dict:
        avail = self.df[self.df["available"] & self.df["price"].notna()]
        pivot = avail.groupby(["product", "platform"])["price"].mean().unstack(fill_value=0)

        summary_lines = ["Comparacion de precios promedio por producto y plataforma:"]
        for product in pivot.index:
            prices = pivot.loc[product]
            cheapest = prices.idxmin()
            most_exp = prices.idxmax()
            summary_lines.append(
                f"  - {product}: mas barato en {cheapest} (${prices[cheapest]:.2f}), "
                f"mas caro en {most_exp} (${prices[most_exp]:.2f})"
            )

        products = pivot.index.tolist()
        chart = {
            "type": "grouped_bar",
            "categories": products,
            "series": {p: pivot[p].tolist() for p in pivot.columns},
            "labels": {"title": "Precio promedio por producto", "x": "Producto", "y": "Precio (MXN)"},
        }
        return {"data": pivot.reset_index(), "summary": "\n".join(summary_lines), "chart_data": chart}

    # ------------------------------------------------------------------
    # c) Fee structure analysis
    # ------------------------------------------------------------------
    def fee_structure_analysis(self) -> dict:
        s = self.df_summary
        fee_by_plat = s.groupby("platform")[["delivery_fee", "service_fee"]].mean()
        fee_by_plat["total_fees"] = fee_by_plat["delivery_fee"] + fee_by_plat["service_fee"]

        fee_by_zone = s.groupby(["platform", "zone_type"])["delivery_fee"].mean().unstack(fill_value=0)

        summary_lines = ["Estructura de fees promedio por plataforma:"]
        for p in fee_by_plat.index:
            row = fee_by_plat.loc[p]
            summary_lines.append(
                f"  - {p}: delivery=${row['delivery_fee']:.2f}, "
                f"service=${row['service_fee']:.2f}, total=${row['total_fees']:.2f}"
            )

        chart = {
            "type": "grouped_bar",
            "categories": fee_by_plat.index.tolist(),
            "series": {
                "Delivery Fee": fee_by_plat["delivery_fee"].tolist(),
                "Service Fee": fee_by_plat["service_fee"].tolist(),
            },
            "labels": {"title": "Fees promedio por plataforma", "x": "Plataforma", "y": "MXN"},
        }
        return {
            "data": fee_by_plat.reset_index(),
            "data_by_zone": fee_by_zone.reset_index(),
            "summary": "\n".join(summary_lines),
            "chart_data": chart,
        }

    # ------------------------------------------------------------------
    # d) Delivery time comparison
    # ------------------------------------------------------------------
    def delivery_time_comparison(self) -> dict:
        s = self.df_summary.dropna(subset=["delivery_time_min"])
        time_by_plat = s.groupby("platform")["delivery_time_min"].mean()
        time_by_city = s.groupby(["platform", "city"])["delivery_time_min"].mean().unstack(fill_value=0)
        time_by_zone = s.groupby(["platform", "zone_type"])["delivery_time_min"].mean().unstack(fill_value=0)

        fastest = time_by_plat.idxmin()
        slowest = time_by_plat.idxmax()

        summary_lines = [
            "Tiempos de entrega promedio:",
            f"  Mas rapido: {fastest} ({time_by_plat[fastest]:.0f} min)",
            f"  Mas lento: {slowest} ({time_by_plat[slowest]:.0f} min)",
        ]
        for p in time_by_plat.index:
            summary_lines.append(f"  - {p}: {time_by_plat[p]:.0f} min promedio")

        chart = {
            "type": "bar_h",
            "categories": time_by_plat.index.tolist(),
            "values": time_by_plat.tolist(),
            "labels": {"title": "Tiempo de entrega promedio", "x": "Minutos", "y": "Plataforma"},
        }
        return {
            "data": time_by_plat.reset_index(),
            "data_by_city": time_by_city.reset_index(),
            "data_by_zone": time_by_zone.reset_index(),
            "summary": "\n".join(summary_lines),
            "chart_data": chart,
        }

    # ------------------------------------------------------------------
    # e) Promotion analysis
    # ------------------------------------------------------------------
    def promotion_analysis(self) -> dict:
        s = self.df_summary
        promo_by_plat = s.groupby("platform")["n_promotions"].agg(["sum", "mean"])
        promo_by_plat.columns = ["total_promotions", "avg_per_address"]

        # Flatten all promotions
        all_promos = {}
        for _, row in self.df.drop_duplicates(subset=["platform", "address_id"]).iterrows():
            plat = row["platform"]
            for promo in row["promotions"]:
                all_promos.setdefault(plat, []).append(promo)

        most_aggressive = promo_by_plat["total_promotions"].idxmax()
        summary_lines = [
            "Analisis de promociones:",
            f"  Plataforma mas agresiva: {most_aggressive} ({int(promo_by_plat.loc[most_aggressive, 'total_promotions'])} promos totales)",
        ]
        for p in promo_by_plat.index:
            summary_lines.append(
                f"  - {p}: {int(promo_by_plat.loc[p, 'total_promotions'])} promos, "
                f"{promo_by_plat.loc[p, 'avg_per_address']:.1f} por direccion"
            )

        return {
            "data": promo_by_plat.reset_index(),
            "all_promotions": all_promos,
            "summary": "\n".join(summary_lines),
            "chart_data": None,
        }

    # ------------------------------------------------------------------
    # f) Geographic analysis
    # ------------------------------------------------------------------
    def geographic_analysis(self) -> dict:
        avail = self.df[self.df["available"] & self.df["price"].notna()]
        price_city = avail.groupby(["city", "platform"])["price"].mean().unstack(fill_value=0)
        price_zone = avail.groupby(["zone_type", "platform"])["price"].mean().unstack(fill_value=0)

        # Where Rappi wins/loses vs cheapest competitor
        rappi_wins = []
        rappi_loses = []
        if "rappi" in price_city.columns:
            for city in price_city.index:
                rappi_p = price_city.loc[city, "rappi"]
                others_min = price_city.loc[city, [c for c in price_city.columns if c != "rappi"]].min()
                if rappi_p <= others_min:
                    rappi_wins.append(city)
                else:
                    rappi_loses.append(city)

        summary_lines = ["Analisis geografico de competitividad:"]
        if rappi_wins:
            summary_lines.append(f"  Rappi mas barato en: {', '.join(rappi_wins)}")
        if rappi_loses:
            summary_lines.append(f"  Rappi mas caro en: {', '.join(rappi_loses)}")

        chart = {
            "type": "heatmap",
            "data": price_city.reset_index().to_dict(orient="list"),
            "labels": {"title": "Precio promedio por ciudad y plataforma", "x": "Plataforma", "y": "Ciudad"},
        }
        return {
            "data_by_city": price_city.reset_index(),
            "data_by_zone": price_zone.reset_index(),
            "rappi_wins": rappi_wins,
            "rappi_loses": rappi_loses,
            "summary": "\n".join(summary_lines),
            "chart_data": chart,
        }

    # ------------------------------------------------------------------
    # g) Total cost analysis
    # ------------------------------------------------------------------
    def total_cost_analysis(self) -> dict:
        avail = self.df[self.df["available"] & self.df["total_cost"].notna()]
        cost_by_plat = avail.groupby("platform")["total_cost"].mean()
        cost_by_prod = avail.groupby(["product", "platform"])["total_cost"].mean().unstack(fill_value=0)

        cheapest = cost_by_plat.idxmin()
        summary_lines = [
            "Costo total promedio para el usuario (producto + delivery + service):",
            f"  Plataforma mas economica: {cheapest} (${cost_by_plat[cheapest]:.2f})",
        ]
        for p in cost_by_plat.index:
            summary_lines.append(f"  - {p}: ${cost_by_plat[p]:.2f}")

        chart = {
            "type": "bar",
            "categories": cost_by_plat.index.tolist(),
            "values": cost_by_plat.tolist(),
            "labels": {"title": "Costo total promedio por plataforma", "x": "Plataforma", "y": "MXN"},
        }
        return {
            "data": cost_by_plat.reset_index(),
            "data_by_product": cost_by_prod.reset_index(),
            "summary": "\n".join(summary_lines),
            "chart_data": chart,
        }

    # ------------------------------------------------------------------
    # h) Top insights
    # ------------------------------------------------------------------
    def generate_top_insights(self, n: int = 5) -> list[dict]:
        insights = []

        prices = self.price_comparison()
        fees = self.fee_structure_analysis()
        times = self.delivery_time_comparison()
        promos = self.promotion_analysis()
        geo = self.geographic_analysis()
        costs = self.total_cost_analysis()

        # 1. Cheapest overall platform
        cost_data = costs["data"]
        if isinstance(cost_data, pd.DataFrame) and not cost_data.empty:
            cheapest_row = cost_data.loc[cost_data["total_cost"].idxmin()]
            insights.append({
                "finding": f"{cheapest_row['platform']} es la plataforma con menor costo total promedio (${cheapest_row['total_cost']:.2f} MXN).",
                "impact": "El costo total incluye producto + delivery fee + service fee, que es lo que realmente paga el usuario.",
                "recommendation": "Si Rappi no es la mas barata, revisar estructura de fees para cerrar la brecha.",
                "supporting_data": costs["data"].to_dict() if isinstance(costs["data"], pd.DataFrame) else costs["data"],
                "chart_data": costs.get("chart_data"),
            })

        # 2. Delivery fee advantage
        fee_data = fees["data"]
        if isinstance(fee_data, pd.DataFrame) and not fee_data.empty:
            cheapest_fee = fee_data.loc[fee_data["delivery_fee"].idxmin()]
            insights.append({
                "finding": f"{cheapest_fee['platform']} tiene el delivery fee mas bajo (${cheapest_fee['delivery_fee']:.2f} MXN promedio).",
                "impact": "El delivery fee es el factor mas visible para el usuario al decidir en que plataforma pedir.",
                "recommendation": "DiDi usa delivery fees bajos como estrategia de penetracion. Evaluar si Rappi puede igualar en zonas estrategicas.",
                "supporting_data": fee_data.to_dict() if isinstance(fee_data, pd.DataFrame) else fee_data,
                "chart_data": fees.get("chart_data"),
            })

        # 3. Delivery time
        time_data = times["data"]
        if isinstance(time_data, pd.DataFrame) and not time_data.empty:
            fastest = time_data.loc[time_data["delivery_time_min"].idxmin()]
            insights.append({
                "finding": f"{fastest['platform']} es la plataforma mas rapida con {fastest['delivery_time_min']:.0f} min promedio.",
                "impact": "El tiempo de entrega impacta directamente la satisfaccion del usuario y la tasa de reorden.",
                "recommendation": "Optimizar rutas y asignacion de repartidores en zonas donde Rappi es mas lento que la competencia.",
                "supporting_data": time_data.to_dict() if isinstance(time_data, pd.DataFrame) else time_data,
                "chart_data": times.get("chart_data"),
            })

        # 4. Geographic competitiveness
        if geo.get("rappi_loses"):
            insights.append({
                "finding": f"Rappi tiene precios mas altos que la competencia en: {', '.join(geo['rappi_loses'])}.",
                "impact": "Estas ciudades representan mercados donde Rappi pierde competitividad en precio.",
                "recommendation": f"Priorizar ajustes de pricing en {', '.join(geo['rappi_loses'][:3])} donde la brecha es mayor.",
                "supporting_data": {"rappi_wins": geo["rappi_wins"], "rappi_loses": geo["rappi_loses"]},
                "chart_data": None,
            })

        # 5. Promotion strategy
        promo_data = promos["data"]
        if isinstance(promo_data, pd.DataFrame) and not promo_data.empty:
            most_agg = promo_data.loc[promo_data["total_promotions"].idxmax()]
            insights.append({
                "finding": f"{most_agg['platform']} lidera en promociones con {int(most_agg['total_promotions'])} promos activas.",
                "impact": "Las promociones son clave para capturar nuevos usuarios y aumentar frecuencia de compra.",
                "recommendation": "Evaluar ROI de las promociones actuales de Rappi y considerar campanas mas agresivas en ciudades donde se pierde cuota.",
                "supporting_data": promo_data.to_dict() if isinstance(promo_data, pd.DataFrame) else promo_data,
                "chart_data": None,
            })

        return insights[:n]
