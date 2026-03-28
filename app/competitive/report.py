"""
Competitive Report Generator - LLM-powered executive competitive intelligence reports.
"""

import json
import logging
from datetime import date

from app.utils.llm import chat_completion

logger = logging.getLogger(__name__)


class CompetitiveReportGenerator:
    """Generates executive competitive intelligence reports.

    Args:
        model: LLM model identifier for OpenRouter.
    """

    def __init__(self, model: str | None = None):
        self.model = model

    def generate_report(self, analyzer) -> str:
        """Generate a full competitive intelligence report using the LLM.

        Args:
            analyzer: CompetitiveAnalyzer instance with data loaded.

        Returns:
            Markdown string with the executive report.
        """
        prices = analyzer.price_comparison()
        fees = analyzer.fee_structure_analysis()
        times = analyzer.delivery_time_comparison()
        promos = analyzer.promotion_analysis()
        geo = analyzer.geographic_analysis()
        costs = analyzer.total_cost_analysis()
        top = analyzer.generate_top_insights()

        n_addresses = analyzer.df["address_id"].nunique()
        n_cities = analyzer.df["city"].nunique()
        platforms = analyzer.df["platform"].unique().tolist()

        analysis_data = {
            "prices_summary": prices["summary"],
            "fees_summary": fees["summary"],
            "times_summary": times["summary"],
            "promos_summary": promos["summary"],
            "geo_summary": geo["summary"],
            "costs_summary": costs["summary"],
            "top_insights": [
                {"finding": i["finding"], "impact": i["impact"], "recommendation": i["recommendation"]}
                for i in top
            ],
            "rappi_wins_cities": geo.get("rappi_wins", []),
            "rappi_loses_cities": geo.get("rappi_loses", []),
        }

        prompt = f"""Genera un informe ejecutivo de inteligencia competitiva para Rappi basado en los siguientes datos de analisis.

## Scope del analisis
- Plataformas comparadas: {', '.join(platforms)}
- Direcciones analizadas: {n_addresses} en {n_cities} ciudades de Mexico
- Productos de referencia: Big Mac, Combo Mediano, McNuggets 10, Coca-Cola 500ml, Agua 1L
- Fuente: scraping competitivo automatizado

## Resultados del analisis
{json.dumps(analysis_data, indent=2, ensure_ascii=False)}

## Instrucciones:
1. Escribe en espanol profesional, tono ejecutivo directo.
2. Estructura del informe:
   - **Resumen Ejecutivo**: 1 parrafo con los 3 hallazgos mas criticos
   - **Metodologia**: scope del analisis (breve)
   - **Posicionamiento de Precios**: comparacion detallada con datos
   - **Estructura de Fees**: delivery fees y service fees por plataforma
   - **Tiempos de Entrega**: ventajas y desventajas por plataforma
   - **Estrategia Promocional**: que hace cada competidor
   - **Variabilidad Geografica**: donde Rappi gana y donde pierde
   - **Top 5 Insights Accionables**: formato finding/impact/recommendation
   - **Recomendaciones Estrategicas**: 3-5 acciones prioritarias
3. Usa Markdown con headers ##, bullets, **bold** en datos clave.
4. Incluye cifras y porcentajes concretos. NO generalices.
5. Maximo 800 palabras."""

        messages = [
            {"role": "system", "content": "Eres un consultor de estrategia competitiva escribiendo un informe para la direccion ejecutiva de Rappi."},
            {"role": "user", "content": prompt},
        ]

        try:
            report = chat_completion(messages, model=self.model, temperature=0.3, max_tokens=4096)
            return report
        except Exception as e:
            logger.error("LLM competitive report failed: %s", e)
            return self._fallback_report(analysis_data, n_addresses, n_cities, platforms)

    def _fallback_report(self, data: dict, n_addresses: int, n_cities: int, platforms: list) -> str:
        lines = [
            "# Informe de Inteligencia Competitiva - Rappi",
            f"\n**Fecha:** {date.today().isoformat()}",
            f"**Scope:** {', '.join(platforms)} | {n_addresses} direcciones | {n_cities} ciudades",
            "",
            "## Posicionamiento de Precios",
            data["prices_summary"],
            "",
            "## Estructura de Fees",
            data["fees_summary"],
            "",
            "## Tiempos de Entrega",
            data["times_summary"],
            "",
            "## Estrategia Promocional",
            data["promos_summary"],
            "",
            "## Analisis Geografico",
            data["geo_summary"],
            "",
            "## Costo Total para el Usuario",
            data["costs_summary"],
            "",
            "## Top Insights Accionables",
        ]
        for i, insight in enumerate(data.get("top_insights", []), 1):
            lines.append(f"\n### {i}. {insight['finding']}")
            lines.append(f"**Impacto:** {insight['impact']}")
            lines.append(f"**Recomendacion:** {insight['recommendation']}")

        return "\n".join(lines)

    @staticmethod
    def generate_pdf_report(markdown_content: str) -> bytes:
        """Convert Markdown report to branded PDF. Returns bytes."""
        from app.utils.pdf import markdown_to_pdf
        subtitle = f"{date.today().strftime('%d de %B de %Y')} | Rappi vs Uber Eats vs DiDi Food - Mexico"
        return markdown_to_pdf("Rappi Competitive Intelligence Report", subtitle, markdown_content)

    @staticmethod
    def generate_html_report(markdown_content: str) -> str:
        """Convert Markdown report to styled HTML with Rappi branding."""
        try:
            import markdown
            body = markdown.markdown(markdown_content, extensions=["tables", "fenced_code"])
        except ImportError:
            import html
            body = f"<pre>{html.escape(markdown_content)}</pre>"

        today = date.today().strftime("%d de %B de %Y")

        return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Rappi Competitive Intelligence Report</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    line-height: 1.6; color: #1a1a2e;
    max-width: 900px; margin: 0 auto; padding: 40px 32px; background: #fff;
  }}
  .report-header {{
    border-bottom: 3px solid #FF441F; padding-bottom: 16px; margin-bottom: 32px;
  }}
  .report-header h1 {{ font-size: 1.8rem; color: #FF441F; margin-bottom: 4px; }}
  .report-header .date {{ color: #6B7280; font-size: 0.9rem; }}
  h2 {{
    color: #FF441F; font-size: 1.3rem; margin-top: 28px; margin-bottom: 12px;
    border-left: 4px solid #FF441F; padding-left: 12px;
  }}
  h3 {{ color: #333; font-size: 1.1rem; margin-top: 20px; margin-bottom: 8px; }}
  ul, ol {{ margin: 8px 0 16px 24px; }}
  li {{ margin-bottom: 6px; }}
  strong {{ color: #1a1a2e; }}
  table {{ width: 100%; border-collapse: collapse; margin: 12px 0; }}
  th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }}
  th {{ background: #FF441F10; color: #FF441F; font-weight: 600; }}
  p {{ margin-bottom: 12px; }}
  @media print {{ body {{ padding: 20px; }} }}
</style>
</head>
<body>
<div class="report-header">
  <h1>Rappi Competitive Intelligence Report</h1>
  <div class="date">{today} | Rappi vs Uber Eats vs DiDi Food - Mexico</div>
</div>
{body}
</body>
</html>"""
