"""
Demo Questions - Reference list for the 30-minute live demo.

Run order: start simple, build complexity, end with wow factor.
"""

DEMO_QUESTIONS = [
    # --- WARM UP (simple, fast) ---
    {
        "question": "Que metricas estan disponibles?",
        "expected": "Lista de 13 metricas con descripciones. Prueba que el bot entiende preguntas basicas.",
        "type": "utilidad",
    },
    {
        "question": "Cuantos paises hay y cuales son?",
        "expected": "9 paises: AR, BR, CL, CO, CR, EC, MX, PE, UY",
        "type": "utilidad",
    },

    # --- FILTRADO Y RANKING ---
    {
        "question": "Cuales son las 5 zonas con peor Perfect Orders esta semana?",
        "expected": "Lista de 5 zonas con peor Perfect Orders (L0W_ROLL). Deberia incluir grafico de barras.",
        "type": "ranking",
    },
    {
        "question": "Top 10 zonas por volumen de ordenes en CO",
        "expected": "Las 10 zonas colombianas con mas ordenes. Chapinero y Usaquen deberian estar arriba.",
        "type": "ranking",
    },

    # --- COMPARACION ---
    {
        "question": "Compara Perfect Orders entre zonas Wealthy y Non Wealthy",
        "expected": "Comparacion por ZONE_TYPE. Wealthy ~0.886, Non Wealthy ~0.844. Grafico de barras.",
        "type": "comparacion",
    },
    {
        "question": "Cual es el promedio de Perfect Orders por pais?",
        "expected": "Tabla con promedio por pais. UY el mejor (~0.90), CR el peor (~0.63).",
        "type": "agregacion",
    },

    # --- TENDENCIAS ---
    {
        "question": "Como ha evolucionado el Perfect Orders promedio en MX las ultimas 8 semanas?",
        "expected": "Serie temporal con tendencia ligeramente al alza. Grafico de linea.",
        "type": "tendencia",
    },

    # --- MULTIVARIABLE (avanzado) ---
    {
        "question": "Que zonas tienen Lead Penetration mayor a 0.7 pero Perfect Orders menor a 0.5?",
        "expected": "Filtro multivariable. Deberia encontrar 1-2 zonas que cumplen ambas condiciones.",
        "type": "multivariable",
    },
    {
        "question": "Que correlacion hay entre Perfect Orders y Lead Penetration?",
        "expected": "Correlacion debil positiva (r~0.04). Scatter plot. Insight: no hay relacion fuerte.",
        "type": "correlacion",
    },

    # --- CONTEXTO DE NEGOCIO (wow factor) ---
    {
        "question": "Cuales son las zonas mas problematicas en Colombia y que recomiendas?",
        "expected": "El bot deberia identificar zonas con peor performance en CO y sugerir analisis adicionales. Muestra capacidad de inferencia.",
        "type": "inferencia",
    },
]


if __name__ == "__main__":
    print("=" * 60)
    print("PREGUNTAS DE DEMO - Rappi AI Intelligence Engine")
    print("=" * 60)
    for i, q in enumerate(DEMO_QUESTIONS, 1):
        print(f"\n{i}. [{q['type'].upper()}]")
        print(f"   Pregunta: {q['question']}")
        print(f"   Esperado: {q['expected']}")
    print(f"\n{'=' * 60}")
    print(f"Total: {len(DEMO_QUESTIONS)} preguntas")
