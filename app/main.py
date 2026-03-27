"""
Rappi AI Intelligence Engine - Streamlit Entry Point.

Main application UI with two modes:
- Case 1: Operational chatbot + automatic insights
- Case 2: Competitive intelligence (scraping + analysis)
"""

import streamlit as st

from app.config import AVAILABLE_MODELS, DEFAULT_MODEL
from app.data.loader import load_raw_data, get_data_summary

# --- Page Config ---
st.set_page_config(
    page_title="Rappi AI Intelligence Engine",
    page_icon="🚀",
    layout="wide",
)

# --- Sidebar ---
st.sidebar.title("Rappi AI Engine")

case = st.sidebar.radio(
    "Selecciona el caso:",
    options=["Caso 1: Operaciones", "Caso 2: Competitive Intelligence"],
)

model_labels = [m["label"] for m in AVAILABLE_MODELS]
model_ids = [m["id"] for m in AVAILABLE_MODELS]
default_idx = next((i for i, m in enumerate(AVAILABLE_MODELS) if m["id"] == DEFAULT_MODEL), 0)

selected_label = st.sidebar.selectbox("Modelo LLM:", model_labels, index=default_idx)
selected_model = model_ids[model_labels.index(selected_label)]

st.sidebar.markdown("---")
st.sidebar.caption(f"Modelo activo: `{selected_model}`")

# --- Main Content ---
st.title("Rappi AI Intelligence Engine")

if case == "Caso 1: Operaciones":
    st.header("Caso 1: Bot Conversacional + Insights Operacionales")
    st.markdown(
        "Analiza métricas operacionales de Rappi: 9 países, 964 zonas, "
        "13 métricas, últimas 8 semanas."
    )

    # Try loading data
    try:
        data = load_raw_data()
        summary = get_data_summary()

        st.success("Datos cargados correctamente.")

        with st.expander("Resumen del dataset", expanded=True):
            st.text(summary)

        st.info("El chatbot y los insights automáticos se implementarán próximamente.")

    except FileNotFoundError:
        st.warning(
            "No se encontró el archivo Excel en `data/raw/`. "
            "Coloca el archivo .xlsx y recarga la página."
        )
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")

else:
    st.header("Caso 2: Competitive Intelligence")
    st.markdown(
        "Scraping competitivo: Rappi vs UberEats vs DiDi Food en México. "
        "Comparación de precios, tiempos de entrega, cobertura y promociones."
    )
    st.info("El sistema de scraping y análisis competitivo se implementará próximamente.")
