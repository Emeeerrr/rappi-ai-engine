# Rappi AI Intelligence Engine

Sistema de inteligencia operacional y competitiva para Rappi, potenciado por IA. Incluye chatbot conversacional sobre datos operativos, motor de insights automáticos con reportes ejecutivos, sistema de scraping competitivo (Rappi vs Uber Eats vs DiDi Food) y análisis de mercado.

![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-red) ![OpenRouter](https://img.shields.io/badge/LLM-OpenRouter-purple)

---

## Tabla de Contenidos

- [Arquitectura del Sistema](#arquitectura-del-sistema)
- [Setup e Instalación](#setup-e-instalacion)
- [Uso](#uso)
- [Ejemplos de Preguntas para el Chatbot](#ejemplos-de-preguntas-para-el-chatbot)
- [Decisiones Técnicas](#decisiones-tecnicas)
- [Estimación de Costos LLM](#estimacion-de-costos-llm)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Limitaciones y Próximos Pasos](#limitaciones-y-proximos-pasos)

---

## Arquitectura del Sistema

```
                                    CASO 1: OPERACIONES
                                    ====================

  Usuario ──> Streamlit UI (Chat) ──> ChatEngine
                                          │
                      ┌───────────────────┼───────────────────┐
                      v                   v                   v
              1. PLANIFICACIÓN     2. EJECUCIÓN        3. RESPUESTA
              (LLM genera JSON     (DataQueryEngine     (LLM sintetiza
               con acciones)        ejecuta queries)     respuesta final)
                      │                   │                   │
                      v                   v                   v
                 OpenRouter          Pandas DFs           OpenRouter
              (Claude/GPT/etc)    (12573 rows metrics)  (Claude/GPT/etc)
                                  (1242 rows orders)


  Usuario ──> Streamlit UI (Insights) ──> InsightsAnalyzer ──> ReportGenerator
                                               │                     │
                                          5 categorías          OpenRouter
                                          de análisis         (reporte ejecutivo)


                                    CASO 2: COMPETITIVE INTELLIGENCE
                                    =================================

  scripts/run_scraping.py ──> Scrapers (Playwright) ──> JSON/CSV
        │                     - RappiScraper                 │
        │                     - UberEatsScraper              v
        │                     - DidiScraper          data/competitive/
        │                            │
        └── --use-fallback ──> FallbackDataGenerator (datos demo realistas)

  Usuario ──> Streamlit UI ──> CompetitiveAnalyzer ──> CompetitiveReportGenerator
                                     │                         │
                               7 tipos de                 OpenRouter
                               análisis                 (informe ejecutivo)
```

### Componentes principales

| Componente | Descripción |
|---|---|
| **ChatEngine** | Pipeline de 2 pasos: el LLM planifica que consultas ejecutar, se ejecutan sobre los DataFrames, y el LLM genera la respuesta final |
| **DataQueryEngine** | 20 métodos de consulta sobre DataFrames (filtrado, ranking, tendencias, correlaciones, etc.) |
| **InsightsAnalyzer** | Detección automática de anomalías, tendencias, benchmarking, correlaciones y oportunidades |
| **CompetitiveAnalyzer** | Comparación de precios, fees, tiempos y promociones entre Rappi, Uber Eats y DiDi Food |
| **ReportGenerator / CompetitiveReportGenerator** | Generación de reportes ejecutivos via LLM en Markdown |
| **BaseScraper + Platform Scrapers** | Scrapers Playwright con rate limiting, retries y user-agent rotation |

---

## Setup e Instalación

### Requisitos

- Python 3.11+
- pip
- Git

### Pasos

```bash
# 1. Clonar el repositorio
git clone <repo-url>
cd rappi-ai-engine

# 2. Crear virtual environment
python -m venv .venv

# 3. Activar virtual environment
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Instalar el paquete en modo desarrollo
pip install -e .

# 6. Configurar variables de entorno
cp .env.example .env
# Editar .env y agregar tu OPENROUTER_API_KEY

# 7. Colocar el archivo Excel
# Copiar el archivo .xlsx a data/raw/

# 8. (Opcional) Instalar Playwright para scraping real
playwright install chromium

# 9. Ejecutar la aplicación
streamlit run app/main.py
```

### Troubleshooting

| Error | Solución |
|---|---|
| `ModuleNotFoundError: No module named 'app'` | Ejecutar `pip install -e .` desde la raíz del proyecto |
| `FileNotFoundError: No .xlsx files found` | Colocar el archivo Excel en `data/raw/` |
| `OPENROUTER_API_KEY not set` | Verificar que `.env` tenga la key correcta |
| `playwright: command not found` | Ejecutar `pip install playwright && playwright install chromium` |

---

## Uso

### Caso 1: Análisis de Operaciones

1. **Chatbot**: Escribe preguntas en lenguaje natural sobre métricas operativas. El bot interpreta la pregunta, consulta los datos y responde con texto + gráficos.
2. **Insights Automáticos**: En la tab "Insights Automáticos", click en "Generar Reporte de Insights" para un análisis automático de anomalías, tendencias y oportunidades.
3. **Exportar**: Cada respuesta con datos incluye un botón "Exportar CSV". El reporte de insights se descarga como Markdown.

### Caso 2: Competitive Intelligence

1. **Generar datos de demo**: En el sidebar selecciona "Competitive Intelligence", luego click en "Generar datos de demo".
2. **O ejecutar scraping via CLI**:
   ```bash
   # Datos de demo (recomendado para la demo)
   python scripts/run_scraping.py --use-fallback

   # Scraping real (requiere Playwright)
   python scripts/run_scraping.py --platform all
   ```
3. **Ver análisis**: Una vez cargados los datos, se muestran métricas clave, gráficos comparativos y la opción de generar el informe ejecutivo completo.

---

## Ejemplos de Preguntas para el Chatbot

### Filtrado y Ranking
- "¿Cuales son las 5 zonas con peor Perfect Orders esta semana?"
- "Top 10 zonas por volumen de ordenes en CO"
- "¿Que zonas hay en Bogota?"

### Comparación
- "Compara Perfect Orders entre zonas Wealthy y Non Wealthy"
- "Compara el Gross Profit UE entre países"
- "¿Como se compara Chapinero vs Usaquén en Perfect Orders?"

### Tendencias
- "Muestra la evolución de Lead Penetration en CO las ultimas 8 semanas"
- "¿Como ha cambiado el Perfect Orders promedio en BR?"
- "¿Cuales son las zonas con mayor crecimiento en ordenes?"

### Agregación
- "¿Cual es el promedio de Pro Adoption por país?"
- "Dame las estadísticas de Lead Penetration en MX"

### Multivariable
- "¿Que zonas tienen Lead Penetration mayor a 0.7 pero Perfect Orders menor a 0.5?"
- "¿Que correlación hay entre Lead Penetration y Perfect Orders?"

### Contexto de negocio
- "¿Cuales son las zonas mas problemáticas en Colombia?"
- "¿Que país tiene mejor performance en general?"

---

## Decisiones Técnicas

### Por que OpenRouter como gateway LLM
- **Model-agnostic**: Permite cambiar entre Claude, GPT-4o y Llama con un solo parámetro, sin cambiar código.
- **Flexibilidad de costos**: El usuario puede elegir modelos mas baratos (Llama) o mas capaces (Claude Sonnet) según la complejidad de la pregunta.
- **API compatible con OpenAI**: Usa el SDK estándar de OpenAI, facilitando migración futura.

### Por que Streamlit
- **Velocidad de desarrollo**: UI funcional en horas vs días con React/Vue.
- **Demo interactiva**: Ideal para una presentación en vivo de 30 minutos.
- **Ecosistema data**: Integración nativa con Pandas, Plotly, DataFrames.

### Por que Plotly para visualizaciones
- **Interactividad**: Zoom, hover, pan sin código adicional.
- **Integración nativa** con `st.plotly_chart`.
- **Gráficos profesionales** con configuración minima.

### Por que Playwright para scraping
- **Headless moderno**: Mejor soporte que Selenium para SPAs modernas.
- **API síncrona y asíncrona**: Flexibilidad según el caso de uso.
- **Multi-browser**: Chromium, Firefox, WebKit.

### Arquitectura de 2 pasos del chatbot
1. **Planificación**: El LLM recibe la pregunta + schema de funciones y genera un plan JSON con que métodos llamar y con que parámetros.
2. **Ejecución + Respuesta**: Se ejecutan las queries sobre los DataFrames reales, y los resultados se pasan al LLM para generar una respuesta rica en lenguaje natural.

**Por que 2 pasos**: Separar planificación de ejecución permite que las queries sean deterministas (Pandas, no LLM) mientras el LLM se enfoca en interpretación y redacción. Esto reduce alucinaciones: los datos siempre son reales.

### Trade-offs asumidos
- **Streamlit vs webapp custom**: Se sacrifica control total de UX por velocidad de desarrollo.
- **Scrapers frágiles**: Los selectores CSS pueden romperse si las plataformas cambian su UI. Se mitiga con el fallback data generator.
- **Datos estáticos**: No hay pipeline de actualización del Excel. En producción se conectaría a un data warehouse.
- **Contexto limitado**: 10 intercambios de memoria conversacional. Suficiente para una sesión, pero no para análisis multidia.

---

## Estimación de Costos LLM

Costos aproximados por sesión via OpenRouter (marzo 2026):

| Escenario | Claude Sonnet 4 | GPT-4o | Llama 4 Maverick |
|---|---|---|---|
| Sesión de chat (10 preguntas) | ~$0.15-0.30 | ~$0.10-0.25 | ~$0.02-0.05 |
| Reporte de insights operativos | ~$0.05-0.15 | ~$0.05-0.10 | ~$0.01-0.02 |
| Informe competitivo | ~$0.05-0.10 | ~$0.05-0.08 | ~$0.01-0.02 |
| **Total sesión completa** | **~$0.25-0.55** | **~$0.20-0.43** | **~$0.04-0.09** |

> Nota: Costos basados en pricing publico de OpenRouter. Varian según longitud de prompts y respuestas.

---

## Estructura del Proyecto

```
rappi-ai-engine/
├── app/
│   ├── main.py                    # Entry point Streamlit (UI completa)
│   ├── config.py                  # Variables de entorno, constantes, modelos
│   ├── __init__.py
│   ├── chatbot/                   # Caso 1: Motor conversacional
│   │   ├── engine.py              # ChatEngine: pipeline planificación -> ejecución -> respuesta
│   │   ├── prompts.py             # System prompt, function schema, response format
│   │   └── memory.py              # ConversationMemory (últimos 10 intercambios)
│   ├── data/                      # Capa de datos
│   │   ├── loader.py              # Carga Excel, validación, cache, get_dataframes()
│   │   ├── queries.py             # DataQueryEngine: 20 métodos de consulta
│   │   └── metrics.py             # Diccionario de 13 métricas con descripciones
│   ├── insights/                  # Caso 1: Insights automáticos
│   │   ├── analyzer.py            # InsightsAnalyzer: 5 categorías de detección
│   │   └── report.py              # ReportGenerator: reportes ejecutivos via LLM
│   ├── scraping/                  # Caso 2: Scraping competitivo
│   │   ├── base.py                # BaseScraper: rate limiting, retries, UA rotation
│   │   ├── rappi.py               # RappiScraper (Playwright)
│   │   ├── ubereats.py            # UberEatsScraper (Playwright)
│   │   ├── didifood.py            # DidiScraper (Playwright)
│   │   ├── addresses.py           # 30 direcciones en 8 ciudades de Mexico
│   │   └── fallback_data.py       # Generador de datos demo realistas (seed=42)
│   ├── competitive/               # Caso 2: Análisis competitivo
│   │   ├── analysis.py            # CompetitiveAnalyzer: 7 tipos de análisis
│   │   └── report.py              # CompetitiveReportGenerator
│   └── utils/
│       └── llm.py                 # Cliente OpenRouter (retries, logging)
├── scripts/
│   ├── run_scraping.py            # CLI para ejecutar scraping o generar datos demo
│   └── demo_questions.py          # Preguntas de referencia para la demo en vivo
├── data/
│   ├── raw/                       # Archivo Excel original (no trackeado en git)
│   ├── processed/                 # CSVs generados
│   └── competitive/               # Datos de scraping competitivo (no trackeados)
├── .env.example                   # Template de variables de entorno
├── .gitignore
├── requirements.txt               # Dependencias Python
├── setup.py                       # Para pip install -e .
├── README.md                      # Este archivo
└── ARCHITECTURE.md                # Documentación de arquitectura
```

---

## Limitaciones y Próximos Pasos

### Limitaciones actuales

- **Dependencia del LLM**: El chatbot depende de la calidad de interpretación del modelo. Queries muy ambiguas o complejas pueden generar planes de ejecución incorrectos.
- **Scraping frágil**: Los selectores CSS de las plataformas pueden cambiar sin aviso, rompiendo los scrapers. El fallback data generator mitiga esto para demos.
- **Datos estáticos**: Los datos operacionales se cargan desde un Excel fijo. No hay pipeline de actualización automática.
- **Memoria limitada**: La memoria conversacional retiene los últimos 10 intercambios (20 mensajes). Sesiones largas pierden contexto.
- **Sin autenticación**: Cualquier usuario con acceso al URL puede usar la aplicación.

### Próximos pasos con mas tiempo

- **RAG sobre documentación interna**: Indexar documentación de métricas, playbooks operativos y guías para enriquecer las respuestas del chatbot.
- **Pipeline de scraping automatizado**: Scheduling con cron/Airflow para recolectar datos competitivos periódicamente.
- **Alertas automáticas**: Notificaciones via email/Slack cuando se detecten anomalías criticas (deterioro >20% en métricas clave).
- **Dashboard de tendencias históricas**: Visualizaciones de evolución de métricas a lo largo del tiempo con forecasting básico.
- **Cache de respuestas frecuentes**: Reducir costos LLM cacheando respuestas a preguntas comunes.
- **Autenticación y roles**: Login con SSO corporativo y permisos por país/region.
- **Deploy en producción**: Streamlit Cloud, Railway o contenedor Docker con CI/CD.

---

## Autor

Prueba Técnica - AI Engineer, Rappi 2025
