"""
Report Generator - Generates executive reports from insights using LLM.

Produces both Markdown (for Streamlit display) and styled HTML (for download).
"""

import json
import logging
from collections import Counter
from datetime import date

from app.utils.llm import chat_completion

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates executive reports from InsightsAnalyzer output.

    Args:
        model: LLM model identifier for OpenRouter.
    """

    def __init__(self, model: str | None = None):
        self.model = model

    def generate_executive_report(self, insights: list[dict]) -> str:
        """Use the LLM to produce a polished executive report in Markdown.

        Args:
            insights: List of insight dicts from InsightsAnalyzer.analyze_all().

        Returns:
            Markdown string with the full report.
        """
        if not insights:
            return "No se detectaron insights significativos en los datos."

        counts = Counter(i["category"] for i in insights)
        severity_counts = Counter(i["severity"] for i in insights)

        # Summarize insights for the LLM (avoid sending too many)
        top_insights = insights[:60]
        insights_summary = []
        for i, ins in enumerate(top_insights, 1):
            insights_summary.append({
                "n": i,
                "category": ins["category"],
                "severity": ins["severity"],
                "title": ins["title"],
                "description": ins["description"],
                "recommendation": ins["recommendation"],
            })

        prompt = f"""Genera un reporte ejecutivo de insights operativos para Rappi basado en los siguientes hallazgos automaticos.

## Datos del analisis
- Total de insights detectados: {len(insights)}
- Por categoria: {dict(counts)}
- Por severidad: {dict(severity_counts)}

## Insights detectados (top {len(insights_summary)}):
{json.dumps(insights_summary, indent=2, ensure_ascii=False)}

## Instrucciones:
1. Escribe en espanol profesional, tono ejecutivo directo.
2. Estructura el reporte asi:
   - **Resumen Ejecutivo**: 1 parrafo con los 3-5 hallazgos mas criticos
   - **Anomalias Detectadas**: los cambios drasticos mas importantes
   - **Tendencias Preocupantes**: deterioros consistentes que requieren atencion
   - **Benchmarking**: zonas rezagadas vs sus pares
   - **Correlaciones**: relaciones entre metricas
   - **Oportunidades**: areas de mejora con alto impacto
   - **Recomendaciones Prioritarias**: top 5 acciones concretas
3. Usa Markdown con headers ##, bullets, **bold** en datos clave.
4. Se conciso pero completo. Cada seccion debe tener 3-5 bullets maximo.
5. Incluye numeros y porcentajes concretos del analisis.
6. NO inventes datos que no esten en los insights proporcionados."""

        messages = [
            {"role": "system", "content": "Eres un consultor senior de operaciones escribiendo un reporte ejecutivo para la direccion de Rappi."},
            {"role": "user", "content": prompt},
        ]

        try:
            report = chat_completion(messages, model=self.model, temperature=0.3, max_tokens=4096)
            return report
        except Exception as e:
            logger.error("LLM report generation failed: %s", e)
            return self._fallback_report(insights)

    def _fallback_report(self, insights: list[dict]) -> str:
        """Generate a basic report without the LLM."""
        counts = Counter(i["category"] for i in insights)
        lines = [
            "# Reporte de Insights Operativos - Rappi",
            f"\n**Fecha:** {date.today().isoformat()}",
            f"\n**Total de insights:** {len(insights)}",
            "",
        ]

        lines.append("## Resumen por Categoria")
        for cat, count in counts.most_common():
            lines.append(f"- **{cat.capitalize()}**: {count} insights")

        for category in ["anomaly", "trend", "benchmark", "correlation", "opportunity"]:
            cat_insights = [i for i in insights if i["category"] == category]
            if not cat_insights:
                continue
            cat_labels = {
                "anomaly": "Anomalias", "trend": "Tendencias Preocupantes",
                "benchmark": "Benchmarking", "correlation": "Correlaciones",
                "opportunity": "Oportunidades",
            }
            lines.append(f"\n## {cat_labels.get(category, category)}")
            for ins in cat_insights[:5]:
                sev = ins['severity'].upper()
                lines.append(f"- **[{sev}]** {ins['title']}")
                lines.append(f"  {ins['description']}")

        lines.append("\n## Recomendaciones Prioritarias")
        critical = [i for i in insights if i["severity"] in ("critical", "high")][:5]
        for j, ins in enumerate(critical, 1):
            lines.append(f"{j}. {ins['recommendation']}")

        return "\n".join(lines)

    @staticmethod
    def generate_pdf_report(markdown_content: str) -> bytes:
        """Convert Markdown report to branded PDF. Returns bytes."""
        from app.utils.pdf import markdown_to_pdf
        subtitle = f"{date.today().strftime('%d de %B de %Y')} | Rappi Operations Intelligence"
        return markdown_to_pdf("Rappi Operations Intelligence Report", subtitle, markdown_content)

    @staticmethod
    def generate_html_report(markdown_content: str) -> str:
        """Convert a Markdown report to styled HTML with Rappi branding."""
        try:
            import markdown
            body = markdown.markdown(markdown_content, extensions=["tables", "fenced_code"])
        except ImportError:
            # Basic conversion if markdown package is not available
            import html
            body = f"<pre>{html.escape(markdown_content)}</pre>"

        today = date.today().strftime("%d de %B de %Y")

        return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Rappi Operations Intelligence Report</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    line-height: 1.6;
    color: #1a1a2e;
    max-width: 900px;
    margin: 0 auto;
    padding: 40px 32px;
    background: #fff;
  }}
  /* Header bar */
  .report-header {{
    border-bottom: 3px solid #FF441F;
    padding-bottom: 16px;
    margin-bottom: 32px;
  }}
  .report-header h1 {{
    font-size: 1.8rem;
    color: #FF441F;
    margin-bottom: 4px;
  }}
  .report-header .date {{
    color: #6B7280;
    font-size: 0.9rem;
  }}
  /* Section headers */
  h2 {{
    color: #FF441F;
    font-size: 1.3rem;
    margin-top: 28px;
    margin-bottom: 12px;
    border-left: 4px solid #FF441F;
    padding-left: 12px;
  }}
  h3 {{
    color: #333;
    font-size: 1.1rem;
    margin-top: 20px;
    margin-bottom: 8px;
  }}
  /* Lists */
  ul, ol {{
    margin: 8px 0 16px 24px;
  }}
  li {{
    margin-bottom: 6px;
  }}
  /* Bold highlights */
  strong {{
    color: #1a1a2e;
  }}
  /* Tables */
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0;
  }}
  th, td {{
    padding: 8px 12px;
    text-align: left;
    border-bottom: 1px solid #e5e7eb;
  }}
  th {{
    background: #FF441F10;
    color: #FF441F;
    font-weight: 600;
  }}
  /* Paragraphs */
  p {{
    margin-bottom: 12px;
  }}
  /* Print styles */
  @media print {{
    body {{ padding: 20px; }}
    .report-header {{ border-bottom-width: 2px; }}
  }}
</style>
</head>
<body>
<div class="report-header">
  <h1>Rappi Operations Intelligence Report</h1>
  <div class="date">{today}</div>
</div>
{body}
</body>
</html>"""
