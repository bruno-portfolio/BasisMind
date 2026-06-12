import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

from basismind.config import (
    SCORING_FISICO_FORTE,
    SCORING_FISICO_FRACO,
    SCORING_FISICO_MUITO_FORTE,
    SCORING_FISICO_MUITO_FRACO,
    SCORING_WEIGHT_CAMBIO,
    SCORING_WEIGHT_COMPETITIVENESS,
    SCORING_WEIGHT_DEMAND,
    SCORING_WEIGHT_LINEUP,
    SCORING_WEIGHT_PREMIUM,
)

BG = "#0B0F17"
SURFACE = "#131A26"
SURFACE_2 = "#1A2332"
BORDER = "#243044"
TEXT = "#E8EDF5"
MUTED = "#8B98AC"
AMBER = "#E8B84B"
GREEN = "#2FBF71"
GREEN_DEEP = "#1A9E5C"
ORANGE = "#F2913D"
RED = "#E5484D"
BLUE = "#4C9AFF"

CLASS_COLORS = {
    "muito_forte": GREEN_DEEP,
    "forte": GREEN,
    "neutro": AMBER,
    "fraco": ORANGE,
    "muito_fraco": RED,
}

CLASS_LABELS = {
    "muito_forte": "VERY STRONG",
    "forte": "STRONG",
    "neutro": "NEUTRAL",
    "fraco": "WEAK",
    "muito_fraco": "VERY WEAK",
}

ACTION_LABELS = {
    "aumentar_forte": "STRONG INCREASE",
    "aumentar": "INCREASE",
    "manter": "HOLD",
    "reduzir": "REDUCE",
    "reduzir_forte": "STRONG REDUCE",
}

ACTION_COLORS = {
    "aumentar_forte": GREEN_DEEP,
    "aumentar": GREEN,
    "manter": AMBER,
    "reduzir": ORANGE,
    "reduzir_forte": RED,
}

INTENSITY_LABELS = {"forte": "strong", "moderada": "moderate", "neutra": "neutral"}

OVERRIDE_LABELS = {
    "logistica": "Logistics",
    "queda_conjunta": "Joint Drop",
    "armadilha_premio": "Premium Trap",
    "competitividade_critica": "Competitiveness",
    "chicago_especulativo": "Chicago Spike",
}

COMPONENT_LABELS = {
    "lineup": "Line-up",
    "premio": "Premium",
    "competitividade": "Competitiveness",
    "demanda": "Demand",
    "cambio": "FX Rate",
}

COMPONENT_WEIGHTS = {
    "lineup": round(SCORING_WEIGHT_LINEUP * 100),
    "premio": round(SCORING_WEIGHT_PREMIUM * 100),
    "competitividade": round(SCORING_WEIGHT_COMPETITIVENESS * 100),
    "demanda": round(SCORING_WEIGHT_DEMAND * 100),
    "cambio": round(SCORING_WEIGHT_CAMBIO * 100),
}

_TEMPLATE = go.layout.Template(
    layout=go.Layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=TEXT, size=13),
        margin=dict(l=10, r=10, t=36, b=10),
        xaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER, linecolor=BORDER),
        yaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER, linecolor=BORDER),
        colorway=[AMBER, BLUE, GREEN, ORANGE, RED, MUTED],
        hoverlabel=dict(bgcolor=SURFACE_2, bordercolor=BORDER, font_color=TEXT),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
)
pio.templates["basismind"] = _TEMPLATE
pio.templates.default = "basismind"

_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
}}

#MainMenu, footer, [data-testid="stToolbar"] {{ visibility: hidden; }}

.block-container {{ padding-top: 2.2rem; padding-bottom: 4rem; }}

h1, h2, h3 {{ letter-spacing: -0.02em; }}

[data-testid="stSidebar"] {{
    background: #080C12;
    border-right: 1px solid {BORDER};
}}

[data-testid="stMetric"] {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 0.9rem 1.1rem;
}}
[data-testid="stMetricValue"] {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.6rem;
}}
[data-testid="stMetricLabel"] {{ color: {MUTED}; }}

.bm-brand {{
    padding: 0.4rem 0 1.1rem 0;
    border-bottom: 1px solid {BORDER};
    margin-bottom: 0.6rem;
}}
.bm-brand .word {{
    font-size: 1.45rem; font-weight: 800; color: {TEXT}; letter-spacing: -0.02em;
}}
.bm-brand .word span {{ color: {AMBER}; }}
.bm-brand .tag {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem; color: {MUTED}; letter-spacing: 0.14em; text-transform: uppercase;
}}

.bm-hero {{
    background: linear-gradient(140deg, {SURFACE} 0%, #0E1420 60%, #11192A 100%);
    border: 1px solid {BORDER};
    border-radius: 16px;
    padding: 2.1rem 2.3rem;
    margin-bottom: 1.4rem;
}}
.bm-hero h1 {{
    margin: 0; font-size: 2.4rem; font-weight: 800; color: {TEXT};
}}
.bm-hero h1 span {{ color: {AMBER}; }}
.bm-hero p {{
    margin: 0.5rem 0 0 0; color: {MUTED}; font-size: 1.05rem; max-width: 46rem;
}}
.bm-chips {{ margin-top: 1.1rem; }}
.bm-chip {{
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: {MUTED};
    border: 1px solid {BORDER};
    border-radius: 999px;
    padding: 0.25rem 0.7rem;
    margin-right: 0.45rem;
}}

.bm-card {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
    height: 100%;
}}
.bm-card .k {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem; color: {AMBER}; letter-spacing: 0.12em; text-transform: uppercase;
}}
.bm-card h4 {{ margin: 0.35rem 0 0.4rem 0; color: {TEXT}; font-size: 1.02rem; }}
.bm-card p {{ margin: 0; color: {MUTED}; font-size: 0.88rem; line-height: 1.45; }}

.bm-action {{
    border-radius: 12px;
    padding: 0.95rem 1.15rem;
    margin-bottom: 0.7rem;
    border: 1px solid {BORDER};
    background: {SURFACE};
    border-left: 4px solid var(--accent);
}}
.bm-action .axis {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem; color: {MUTED}; letter-spacing: 0.14em; text-transform: uppercase;
}}
.bm-action .act {{
    font-size: 1.18rem; font-weight: 700; color: var(--accent); margin: 0.1rem 0;
}}
.bm-action .sub {{ font-size: 0.82rem; color: {MUTED}; }}

.bm-ov {{
    display: inline-block;
    font-size: 0.74rem; font-weight: 600;
    border-radius: 999px;
    padding: 0.28rem 0.75rem;
    margin: 0 0.4rem 0.4rem 0;
    border: 1px solid {BORDER};
    color: {MUTED};
    background: {SURFACE};
}}
.bm-ov.on {{
    color: #fff; background: {RED}; border-color: {RED};
}}

.bm-note {{
    border: 1px dashed {BORDER};
    border-radius: 12px;
    padding: 0.8rem 1rem;
    color: {MUTED};
    font-size: 0.86rem;
    background: rgba(232, 184, 75, 0.04);
}}
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def sidebar_brand() -> None:
    st.sidebar.markdown(
        """
        <div class="bm-brand">
            <div class="word">🌾 Basis<span>Mind</span></div>
            <div class="tag">Grain Trading Intelligence</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def plot(fig: go.Figure) -> None:
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def hero(title_html: str, tagline: str, chips: list[str]) -> None:
    chips_html = "".join(f'<span class="bm-chip">{c}</span>' for c in chips)
    st.markdown(
        f"""
        <div class="bm-hero">
            <h1>{title_html}</h1>
            <p>{tagline}</p>
            <div class="bm-chips">{chips_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def card(kicker: str, title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="bm-card">
            <div class="k">{kicker}</div>
            <h4>{title}</h4>
            <p>{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def action_card(axis: str, acao: str, sub: str) -> None:
    color = ACTION_COLORS.get(acao, AMBER)
    label = ACTION_LABELS.get(acao, acao.upper())
    st.markdown(
        f"""
        <div class="bm-action" style="--accent: {color};">
            <div class="axis">{axis}</div>
            <div class="act">{label}</div>
            <div class="sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def recommendation_cards(report) -> None:
    action_card(
        "Physical position",
        report.recomendacao_fisica["acao"],
        f"sizing {report.recomendacao_fisica['sizing_pct']:+.0f}% · "
        f"{INTENSITY_LABELS[report.recomendacao_fisica['intensidade']]} intensity",
    )
    action_card(
        "Chicago hedge",
        report.recomendacao_hedge["acao"],
        f"delta {report.recomendacao_hedge['delta_pp']:+.0f}pp vs target · "
        f"{INTENSITY_LABELS[report.recomendacao_hedge['intensidade']]} intensity",
    )


def override_chips(active: list[str]) -> None:
    html = "".join(
        f'<span class="bm-ov {"on" if key in active else ""}">{label}</span>'
        for key, label in OVERRIDE_LABELS.items()
    )
    st.markdown(html, unsafe_allow_html=True)


def note(text: str) -> None:
    st.markdown(f'<div class="bm-note">{text}</div>', unsafe_allow_html=True)


def score_gauge(score: float, classificacao: str, height: int = 260) -> go.Figure:
    color = CLASS_COLORS.get(classificacao, AMBER)
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number=dict(
                font=dict(family="JetBrains Mono, monospace", size=44, color=TEXT),
                valueformat=".0f",
            ),
            title=dict(
                text=CLASS_LABELS.get(classificacao, classificacao.upper()),
                font=dict(size=15, color=color),
            ),
            gauge=dict(
                axis=dict(range=[0, 100], tickcolor=MUTED, tickfont=dict(size=10)),
                bar=dict(color=color, thickness=0.32),
                bgcolor=SURFACE_2,
                borderwidth=0,
                steps=[
                    dict(
                        range=[0, SCORING_FISICO_MUITO_FRACO],
                        color="rgba(229, 72, 77, 0.28)",
                    ),
                    dict(
                        range=[SCORING_FISICO_MUITO_FRACO, SCORING_FISICO_FRACO],
                        color="rgba(242, 145, 61, 0.22)",
                    ),
                    dict(
                        range=[SCORING_FISICO_FRACO, SCORING_FISICO_FORTE],
                        color="rgba(232, 184, 75, 0.14)",
                    ),
                    dict(
                        range=[SCORING_FISICO_FORTE, SCORING_FISICO_MUITO_FORTE],
                        color="rgba(47, 191, 113, 0.20)",
                    ),
                    dict(
                        range=[SCORING_FISICO_MUITO_FORTE, 100],
                        color="rgba(26, 158, 92, 0.30)",
                    ),
                ],
            ),
        )
    )
    fig.update_layout(height=height, margin=dict(l=24, r=24, t=44, b=8))
    return fig


def contribution_waterfall(
    componentes: dict, score: float, height: int = 300
) -> go.Figure:
    names = [COMPONENT_LABELS[k] for k in COMPONENT_WEIGHTS]
    contributions = [
        componentes[k]["score"] * COMPONENT_WEIGHTS[k] / 100 for k in COMPONENT_WEIGHTS
    ]
    fig = go.Figure(
        go.Waterfall(
            orientation="v",
            x=names + ["Score"],
            y=contributions + [score],
            measure=["relative"] * len(names) + ["total"],
            text=[f"{v:.1f}" for v in contributions] + [f"{score:.1f}"],
            textposition="outside",
            textfont=dict(family="JetBrains Mono, monospace", size=12),
            connector=dict(line=dict(color=BORDER, width=1)),
            increasing=dict(marker=dict(color=BLUE)),
            totals=dict(marker=dict(color=AMBER)),
        )
    )
    fig.update_layout(
        height=height,
        yaxis=dict(range=[0, 105], title=None),
        showlegend=False,
        title=dict(
            text="weight x component score = contribution",
            font=dict(size=12, color=MUTED),
        ),
    )
    return fig
