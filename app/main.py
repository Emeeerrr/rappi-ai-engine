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
    st.markdown("---")
    st.caption("Powered by OpenRouter")


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

    # ---- Scrollable chat area ----
    chat_area = st.container(height=320)
    with chat_area:
        if not st.session_state.chat_history:
            # Suggested questions (centered, ChatGPT-style)
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
            # Render all messages
            for i, msg in enumerate(st.session_state.chat_history):
                if msg["role"] == "user":
                    _render_user_message(msg["content"])
                else:
                    _render_assistant_message(msg, i)
                    if msg.get("error"):
                        st.error(msg["error"])

    # ---- Input bar (model selector + text input + send) pinned below chat ----
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

else:
    st.title("Competitive Intelligence")
    st.info(
        "Esta seccion esta en desarrollo. Aqui se implementara el scraping competitivo "
        "de Rappi vs UberEats vs DiDi Food, con comparacion de precios, tiempos de entrega, "
        "cobertura y promociones."
    )
