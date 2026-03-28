# Arquitectura - Rappi AI Intelligence Engine

## Flujo del Chatbot (Caso 1)

```
Usuario escribe pregunta
        │
        v
┌─────────────────────────────────────────────┐
│  PASO 1: PLANIFICACION                       │
│                                              │
│  Input:  system_prompt + function_schema     │
│          + historial + pregunta              │
│  LLM ->  JSON {                              │
│            thinking: "...",                   │
│            actions: [                         │
│              {function: "top_zones_by_metric",│
│               params: {metric: "...", n: 5}} │
│            ],                                │
│            direct_response: null              │
│          }                                   │
└─────────────────┬───────────────────────────┘
                  │
                  v
┌─────────────────────────────────────────────┐
│  PASO 2: EJECUCION                           │
│                                              │
│  Para cada accion en el plan:                │
│    DataQueryEngine.metodo(**params)           │
│    -> {success, data, summary, chart_data}   │
│                                              │
│  Los datos vienen de Pandas DataFrames       │
│  (nunca del LLM = no hay alucinaciones)      │
└─────────────────┬───────────────────────────┘
                  │
                  v
┌─────────────────────────────────────────────┐
│  PASO 3: GENERACION DE RESPUESTA             │
│                                              │
│  Input:  summaries de las queries            │
│          + pregunta original                 │
│          + instrucciones de formato           │
│  LLM ->  Respuesta en lenguaje natural       │
│          con datos reales, contextualizada   │
└─────────────────┬───────────────────────────┘
                  │
                  v
        UI muestra: texto + graficos + export CSV
```

### Por que 2 pasos

El LLM **nunca toca los datos directamente**. Solo decide que consultar (paso 1) y como redactar la respuesta (paso 3). La ejecucion real (paso 2) es determinista via Pandas. Esto:

- Elimina alucinaciones en datos numericos
- Permite auditar exactamente que se consulto
- Hace el sistema extensible (agregar un metodo al DataQueryEngine lo hace disponible al chatbot automaticamente)

---

## Flujo de Insights Automaticos (Caso 1)

```
Click "Generar Reporte"
        │
        v
┌─────────────────────────────────────────────┐
│  InsightsAnalyzer.analyze_all()              │
│                                              │
│  5 categorias de deteccion:                  │
│  a) Anomalias     (L0W vs L1W, >10% cambio) │
│  b) Tendencias    (deterioro 3+ semanas)     │
│  c) Benchmarking  (zona vs peers, >1.5 std)  │
│  d) Correlaciones (pares r > 0.5)            │
│  e) Oportunidades (alto volumen + baja calidad│
│                    paises bajo promedio, etc.)│
│                                              │
│  Output: lista de insights ordenados         │
│          por severidad (critical > high > ...) │
└─────────────────┬───────────────────────────┘
                  │
                  v
┌─────────────────────────────────────────────┐
│  ReportGenerator.generate_executive_report()  │
│                                              │
│  LLM recibe los insights crudos y genera:    │
│  - Resumen ejecutivo                         │
│  - Secciones por categoria                   │
│  - Recomendaciones prioritarias              │
│  - Formato Markdown ejecutivo                │
└─────────────────┬───────────────────────────┘
                  │
                  v
        UI muestra: metricas + reporte + descarga
```

---

## Flujo de Scraping + Analisis (Caso 2)

```
scripts/run_scraping.py
        │
        ├── --use-fallback ──> FallbackDataGenerator
        │                      (datos realistas, seed=42,
        │                       90 records: 3 plataformas x 30 dirs)
        │
        └── --platform all ──> BaseScraper.run_all()
                               ├── RappiScraper    (Playwright)
                               ├── UberEatsScraper (Playwright)
                               └── DidiScraper     (Playwright)
                                        │
                                        v
                               data/competitive/
                               ├── competitive_data.json
                               └── competitive_data.csv
                                        │
                                        v
                            ┌───────────────────────────┐
                            │  CompetitiveAnalyzer       │
                            │                           │
                            │  7 analisis:              │
                            │  - price_comparison       │
                            │  - fee_structure_analysis  │
                            │  - delivery_time_comparison│
                            │  - promotion_analysis     │
                            │  - geographic_analysis    │
                            │  - total_cost_analysis    │
                            │  - generate_top_insights  │
                            └─────────────┬─────────────┘
                                          │
                                          v
                            CompetitiveReportGenerator
                            (LLM -> informe ejecutivo Markdown)
```

---

## DataQueryEngine - 20 metodos disponibles

| Categoria | Metodos |
|---|---|
| Filtrado y Ranking | `top_zones_by_metric`, `bottom_zones_by_metric`, `filter_zones` |
| Comparaciones | `compare_metric_by_group`, `compare_zones` |
| Tendencias | `get_zone_trend`, `get_aggregated_trend` |
| Agregaciones | `aggregate_metric`, `get_metric_stats` |
| Multivariable | `multi_metric_filter`, `correlate_metrics` |
| Ordenes | `get_orders_trend`, `top_zones_by_orders`, `orders_growth` |
| Utilidades | `list_countries`, `list_cities`, `list_zones`, `list_metrics`, `search_zone`, `get_week_columns` |

Cada metodo retorna: `{success: bool, data: DataFrame|value, summary: str, chart_data: dict|None}`
