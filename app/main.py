"""
Rappi AI Intelligence Engine - Streamlit Entry Point.

Chat UI styled like ChatGPT/Claude: scrollable chat area, user messages
right-aligned, assistant left-aligned, input bar pinned to the bottom.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from app.config import AVAILABLE_MODELS, DEFAULT_MODEL

# ------------------------------------------------------------------
# Page config (must be first Streamlit call)
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Rappi AI Intelligence Engine",
    page_icon="\U0001F680",
    layout="wide",
)

# ------------------------------------------------------------------
# Custom CSS
# ------------------------------------------------------------------
st.markdown("""
<style>
    :root {
        --rappi-orange: #FF441F;
        --rappi-gray: #6B7280;
    }
    /* Sidebar title */
    [data-testid="stSidebar"] h1 {
        color: #FF441F;
        font-size: 1.4rem;
    }

    /* ---- User message bubble (right-aligned) ---- */
    .user-row {
        display: flex;
        justify-content: flex-end;
        align-items: flex-start;
        gap: 10px;
        margin: 0.75rem 0;
    }
    .user-bubble {
        background: #FF441F12;
        border: 1px solid #FF441F30;
        border-radius: 16px 16px 4px 16px;
        padding: 12px 16px;
        max-width: 75%;
        line-height: 1.5;
        white-space: pre-wrap;
    }
    .user-avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: #FF441F;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        flex-shrink: 0;
    }

    /* ---- Suggested-question buttons ---- */
    .suggestion-row button {
        border: 1px solid #FF441F !important;
        border-radius: 8px !important;
        color: #FF441F !important;
        background: transparent !important;
        font-size: 0.85rem !important;
        transition: all 0.2s !important;
    }
    .suggestion-row button:hover {
        background: #FF441F !important;
        color: white !important;
    }

    /* ---- Input bar area ---- */
    .input-bar-area .stSelectbox, .input-bar-area .stTextInput, .input-bar-area .stButton {
        margin-bottom: 0 !important;
    }
    .input-bar-area .stButton > button {
        background: #FF441F !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-size: 1.1rem !important;
        height: 42px !important;
    }
    .input-bar-area .stButton > button:hover {
        background: #e03a1a !important;
    }

    /* ---- Expander style ---- */
    .streamlit-expanderHeader {
        font-size: 0.8rem;
        color: var(--rappi-gray);
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------
# Plotly theme defaults
# ------------------------------------------------------------------
RAPPI_ORANGE = "#FF441F"
PLOTLY_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", size=12),
    xaxis=dict(showgrid=True, gridcolor="rgba(200,200,200,0.3)"),
    yaxis=dict(showgrid=True, gridcolor="rgba(200,200,200,0.3)"),
    margin=dict(l=40, r=20, t=50, b=40),
)


def render_chart(chart_data: dict) -> go.Figure | None:
    """Build a Plotly figure from a chart_data dict."""
    if not chart_data:
        return None

    chart_type = chart_data.get("type", "bar")
    x = chart_data.get("x", [])
    y = chart_data.get("y", [])
    labels = chart_data.get("labels", {})
    title = labels.get("title", "")
    x_label = labels.get("x", "")
    y_label = labels.get("y", "")

    fig = None

    if chart_type == "bar":
        fig = px.bar(x=x, y=y, labels={"x": x_label, "y": y_label}, title=title)
        fig.update_traces(marker_color=RAPPI_ORANGE)
    elif chart_type == "line":
        if isinstance(y, dict):
            fig = go.Figure()
            colors = [RAPPI_ORANGE, "#3B82F6", "#10B981", "#F59E0B", "#8B5CF6",
                      "#EC4899", "#6366F1", "#14B8A6"]
            for i, (name, values) in enumerate(y.items()):
                fig.add_trace(go.Scatter(
                    x=x, y=values, mode="lines+markers", name=name,
                    line=dict(color=colors[i % len(colors)], width=2),
                ))
            fig.update_layout(title=title, xaxis_title=x_label, yaxis_title=y_label)
        else:
            fig = px.line(x=x, y=y, labels={"x": x_label, "y": y_label},
                          title=title, markers=True)
            fig.update_traces(line_color=RAPPI_ORANGE)
    elif chart_type == "scatter":
        fig = px.scatter(x=x, y=y, labels={"x": x_label, "y": y_label}, title=title)
        fig.update_traces(marker=dict(color=RAPPI_ORANGE, size=6, opacity=0.7))

    if fig:
        fig.update_layout(**PLOTLY_LAYOUT)
    return fig


# ------------------------------------------------------------------
# Session state init
# ------------------------------------------------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "selected_model" not in st.session_state:
    st.session_state.selected_model = DEFAULT_MODEL
if "chat_engine" not in st.session_state:
    st.session_state.chat_engine = None
if "pending_message" not in st.session_state:
    st.session_state.pending_message = None
if "input_key" not in st.session_state:
    st.session_state.input_key = 0


def _get_engine():
    """Lazy-init the ChatEngine."""
    if st.session_state.chat_engine is None:
        from app.chatbot.engine import ChatEngine
        st.session_state.chat_engine = ChatEngine(model=st.session_state.selected_model)
    return st.session_state.chat_engine


# ------------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------------
with st.sidebar:
    st.markdown("# Rappi AI Engine")
    case = st.radio(
        "Selecciona el caso:",
        options=["Analisis de Operaciones", "Competitive Intelligence"],
    )
    st.divider()
    if st.button("Limpiar conversacion", width="stretch"):
        st.session_state.chat_history = []
        if st.session_state.chat_engine is not None:
            st.session_state.chat_engine.clear_memory()
        st.rerun()


# ------------------------------------------------------------------
# Helper: render a single user message (right-aligned HTML bubble)
# ------------------------------------------------------------------
def _render_user_message(content: str):
    import html
    safe = html.escape(content)
    st.markdown(
        f'<div class="user-row">'
        f'  <div class="user-bubble">{safe}</div>'
        f'  <div class="user-avatar">U</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------------
# Helper: render a single assistant message (left-aligned, native)
# ------------------------------------------------------------------
def _render_assistant_message(msg: dict, msg_index: int):
    with st.chat_message("assistant", avatar="\U0001F916"):
        st.markdown(msg["content"])
        for c_idx, chart_data in enumerate(msg.get("charts", [])):
            fig = render_chart(chart_data)
            if fig:
                st.plotly_chart(fig, width="stretch", key=f"chart_{msg_index}_{c_idx}")
        for j, df in enumerate(msg.get("raw_data", [])):
            if isinstance(df, pd.DataFrame) and not df.empty:
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Exportar CSV", data=csv,
                    file_name=f"rappi_data_{msg_index}_{j}.csv",
                    mime="text/csv",
                    key=f"hist_dl_{msg_index}_{j}",
                )
        if msg.get("actions"):
            with st.expander("Ver detalle tecnico"):
                st.markdown(f"**Modelo:** `{st.session_state.selected_model}`")
                st.markdown(f"**Metodos ejecutados:** {', '.join(msg['actions'])}")


# ------------------------------------------------------------------
# Process pending message (runs once at the top of each rerun)
# ------------------------------------------------------------------
if st.session_state.pending_message is not None:
    _pending = st.session_state.pending_message
    st.session_state.pending_message = None  # clear immediately to avoid re-processing

    st.session_state.chat_history.append({
        "role": "user", "content": _pending,
        "charts": [], "raw_data": [], "actions": [],
    })
    engine = _get_engine()
    with st.spinner("Analizando..."):
        result = engine.process_query(_pending)

    st.session_state.chat_history.append({
        "role": "assistant",
        "content": result.get("response", ""),
        "charts": result.get("charts", []),
        "raw_data": result.get("raw_data", []),
        "actions": result.get("actions_executed", []),
        "error": result.get("error"),
    })


# ------------------------------------------------------------------
# Main content
# ------------------------------------------------------------------
if case == "Analisis de Operaciones":
    st.title("Rappi AI Intelligence Engine")
    st.caption("Analiza metricas operacionales: 9 paises, 964 zonas, 13 metricas, 9 semanas")

    tab_chat, tab_insights = st.tabs(["Chat", "Insights Automaticos"])

    # ==================================================================
    # TAB: Chat
    # ==================================================================
    with tab_chat:
        chat_area = st.container(height=320)
        with chat_area:
            if not st.session_state.chat_history:
                st.markdown("")
                st.markdown("")
                st.markdown("#### Prueba alguna de estas preguntas:")
                engine = _get_engine()
                suggestions = engine.get_suggested_questions()
                st.markdown('<div class="suggestion-row">', unsafe_allow_html=True)
                cols = st.columns(len(suggestions))
                for idx, (col, question) in enumerate(zip(cols, suggestions)):
                    with col:
                        if st.button(question, key=f"sug_{idx}", width="stretch"):
                            st.session_state.pending_message = question
                            st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                for i, msg in enumerate(st.session_state.chat_history):
                    if msg["role"] == "user":
                        _render_user_message(msg["content"])
                    else:
                        _render_assistant_message(msg, i)
                        if msg.get("error"):
                            st.error(msg["error"])

        # Input bar
        st.markdown('<div class="input-bar-area">', unsafe_allow_html=True)
        col_model, col_input, col_send = st.columns([1.2, 5, 0.4])

        model_labels = [m["label"] for m in AVAILABLE_MODELS]
        model_ids = [m["id"] for m in AVAILABLE_MODELS]
        default_idx = next((i for i, m in enumerate(AVAILABLE_MODELS)
                            if m["id"] == st.session_state.selected_model), 0)

        with col_model:
            selected_label = st.selectbox(
                "Modelo", model_labels, index=default_idx, label_visibility="collapsed",
            )
            new_model = model_ids[model_labels.index(selected_label)]
            if new_model != st.session_state.selected_model:
                st.session_state.selected_model = new_model
                if st.session_state.chat_engine is not None:
                    st.session_state.chat_engine.set_model(new_model)
        with col_input:
            user_input = st.text_input(
                "Mensaje", placeholder="Pregunta sobre las operaciones de Rappi...",
                label_visibility="collapsed", key=f"chat_input_{st.session_state.input_key}",
            )
        with col_send:
            send_clicked = st.button("\u27A4", width="stretch")
        st.markdown('</div>', unsafe_allow_html=True)

        if (send_clicked or user_input) and user_input:
            st.session_state.pending_message = user_input
            st.session_state.input_key += 1
            st.rerun()

    # ==================================================================
    # TAB: Insights Automaticos
    # ==================================================================
    with tab_insights:
        if st.button("Generar Reporte de Insights", type="primary", key="gen_insights"):
            from app.data.loader import get_dataframes
            from app.insights.analyzer import InsightsAnalyzer
            from app.insights.report import ReportGenerator

            df_m, df_o, _ = get_dataframes()
            analyzer = InsightsAnalyzer(df_m, df_o)

            with st.spinner("Analizando datos... esto puede tomar unos segundos"):
                all_insights = analyzer.analyze_all()

            st.session_state.insights_data = all_insights

            with st.spinner("Generando reporte ejecutivo con IA..."):
                gen = ReportGenerator(model=st.session_state.selected_model)
                report_md = gen.generate_executive_report(all_insights)
                report_html = gen.generate_html_report(report_md)

            st.session_state.insights_report_md = report_md
            st.session_state.insights_report_html = report_html
            st.rerun()

        # Show cached results if available
        if "insights_data" in st.session_state and st.session_state.insights_data:
            all_insights = st.session_state.insights_data
            from collections import Counter
            counts = Counter(i["category"] for i in all_insights)
            sev_counts = Counter(i["severity"] for i in all_insights)

            cols = st.columns(5)
            cat_labels = {
                "anomaly": "Anomalias", "trend": "Tendencias",
                "benchmark": "Benchmarking", "correlation": "Correlaciones",
                "opportunity": "Oportunidades",
            }
            for col_w, (cat, label) in zip(cols, cat_labels.items()):
                col_w.metric(label, counts.get(cat, 0))

            st.markdown(
                f"**Total:** {len(all_insights)} insights | "
                f"Criticos: {sev_counts.get('critical', 0)}, "
                f"Altos: {sev_counts.get('high', 0)}, "
                f"Medios: {sev_counts.get('medium', 0)}, "
                f"Bajos: {sev_counts.get('low', 0)}"
            )
            st.divider()

        if "insights_report_md" in st.session_state and st.session_state.insights_report_md:
            st.markdown(st.session_state.insights_report_md)

            st.divider()
            st.download_button(
                label="Descargar Reporte",
                data=st.session_state.insights_report_md,
                file_name="rappi_insights_report.md",
                mime="text/markdown",
                key="dl_md_report",
            )

            # Charts from insights
            chart_insights = [
                i for i in st.session_state.insights_data if i.get("chart_data")
            ]
            if chart_insights:
                st.divider()
                st.markdown("### Visualizaciones")
                for ci_idx, ins in enumerate(chart_insights[:10]):
                    fig = render_chart(ins["chart_data"])
                    if fig:
                        st.plotly_chart(fig, width="stretch", key=f"ins_chart_{ci_idx}")

            # Raw insights table
            with st.expander("Ver todos los insights (raw)"):
                table_data = []
                for ins in st.session_state.insights_data:
                    table_data.append({
                        "Severidad": ins["severity"],
                        "Categoria": ins["category"],
                        "Titulo": ins["title"],
                        "Zonas": ", ".join(ins["zones"][:3]) if ins["zones"] else "-",
                        "Metricas": ", ".join(ins["metrics"][:2]),
                    })
                st.dataframe(pd.DataFrame(table_data), use_container_width=True)

else:
    st.title("Competitive Intelligence")
    st.caption("Rappi vs Uber Eats vs DiDi Food - Comparacion de precios, fees y tiempos en Mexico")

    st.info(
        "El scraping se ejecuta via script por temas de tiempo y bloqueo de plataformas. "
        "Ejecuta `python scripts/run_scraping.py --use-fallback` para generar datos de demo, "
        "o usa el boton de abajo."
    )

    # Session state for competitive data
    if "competitive_data" not in st.session_state:
        st.session_state.competitive_data = None

    col_load, col_gen = st.columns(2)

    with col_load:
        if st.button("Cargar datos competitivos", width="stretch"):
            import json
            from pathlib import Path
            data_dir = Path("data/competitive")
            json_path = data_dir / "competitive_data.json"
            if json_path.exists():
                with open(json_path, encoding="utf-8") as f:
                    st.session_state.competitive_data = json.load(f)
                st.rerun()
            else:
                st.warning("No se encontraron datos en data/competitive/. Genera datos de demo primero.")

    with col_gen:
        if st.button("Generar datos de demo", width="stretch"):
            with st.spinner("Generando datos de demo..."):
                from app.scraping.fallback_data import generate_fallback_data
                from app.scraping.base import BaseScraper
                results = generate_fallback_data()
                BaseScraper.save_results(results, "data/competitive")
                st.session_state.competitive_data = results
            st.rerun()

    # Display loaded data
    if st.session_state.competitive_data:
        data = st.session_state.competitive_data
        platforms = sorted(set(r["platform"] for r in data))
        cities = sorted(set(r["city"] for r in data))
        addresses = sorted(set(r["address_id"] for r in data))

        st.divider()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Registros", len(data))
        c2.metric("Plataformas", len(platforms))
        c3.metric("Ciudades", len(cities))
        c4.metric("Direcciones", len(addresses))

        # Flatten to DataFrame for preview
        rows = []
        for r in data:
            for p in r.get("products", []):
                rows.append({
                    "Plataforma": r["platform"],
                    "Ciudad": r["city"],
                    "Zona": r["address_label"],
                    "Tipo": r["zone_type"],
                    "Producto": p["name"],
                    "Precio": p.get("price"),
                    "Disponible": p.get("available"),
                    "Delivery Fee": r.get("delivery_fee"),
                    "Service Fee": r.get("service_fee"),
                    "Tiempo Entrega": r.get("estimated_delivery_time"),
                    "Total Big Mac": r.get("total_price_big_mac_combo"),
                })
        if rows:
            df_comp = pd.DataFrame(rows)
            st.dataframe(df_comp, use_container_width=True, height=400)

        st.caption("El analisis competitivo detallado y reporte se implementaran en la siguiente fase.")
