import streamlit as st
import sys
from pathlib import Path
from datetime import date
import json

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "data"))

from engine import DecisionEngine, MarketInputs, DecisionReport
from book import BookState

st.set_page_config(page_title="Decision Engine | BasisMind", page_icon="🎯", layout="wide")

st.markdown("""
<style>
    .scenario-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 1rem;
    }
    .score-display {
        font-size: 3rem;
        font-weight: 700;
        text-align: center;
        padding: 1rem;
        border-radius: 12px;
    }
    .score-muito-forte { background: #d4edda; color: #155724; }
    .score-forte { background: #c3e6cb; color: #155724; }
    .score-neutro { background: #fff3cd; color: #856404; }
    .score-fraco { background: #f5c6cb; color: #721c24; }
    .score-muito-fraco { background: #f8d7da; color: #721c24; }

    .rec-box {
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        color: white;
        font-weight: 500;
    }
    .rec-aumentar { background: #28a745; border-left: 4px solid #1e7e34; }
    .rec-manter { background: #fd7e14; border-left: 4px solid #e76800; color: white; }
    .rec-reduzir { background: #dc3545; border-left: 4px solid #bd2130; }

    .override-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0.2rem;
    }
    .override-active { background: #dc3545; color: white; }
    .override-inactive { background: #6c757d; color: white; }

    .component-bar {
        height: 24px;
        border-radius: 4px;
        margin: 4px 0;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎯 Decision Engine in Action")
st.markdown("See how the engine responds to different market scenarios.")

SCENARIOS = {
    "normal": {
        "nome": "📈 Normal Market",
        "descricao": "Crop season underway, balanced indicators",
        "inputs": MarketInputs(
            dt=date(2024, 5, 15),
            var_semanal_lineup=5.0,
            percentil_premium=65.0,
            spread_adjusted=-5.0,
            z_pace=0.3,
            var_cambio_5d=-0.5,
            chicago_percentile=55.0,
            chicago_is_spike=False,
            logistics_flag_active=False,
            logistics_reason=None,
        ),
        "book": None,
    },
    "oportunidade": {
        "nome": "🚀 Great Opportunity",
        "descricao": "Strong lineup, high premium, Brazil competitive",
        "inputs": MarketInputs(
            dt=date(2024, 6, 1),
            var_semanal_lineup=15.0,
            percentil_premium=82.0,
            spread_adjusted=-18.0,
            z_pace=1.2,
            var_cambio_5d=-2.0,
            chicago_percentile=70.0,
            chicago_is_spike=False,
            logistics_flag_active=False,
            logistics_reason=None,
        ),
        "book": None,
    },
    "queda_conjunta": {
        "nome": "📉 Override: Joint Drop",
        "descricao": "Lineup plunging AND premium falling - market exiting",
        "inputs": MarketInputs(
            dt=date(2024, 4, 20),
            var_semanal_lineup=-15.0,
            percentil_premium=25.0,
            spread_adjusted=5.0,
            z_pace=-0.8,
            var_cambio_5d=1.5,
            chicago_percentile=40.0,
            chicago_is_spike=False,
            logistics_flag_active=False,
            logistics_reason=None,
        ),
        "book": None,
    },
    "armadilha": {
        "nome": "⚠️ Override: Premium Trap",
        "descricao": "High premium BUT lineup falling - price will correct",
        "inputs": MarketInputs(
            dt=date(2024, 5, 10),
            var_semanal_lineup=-12.0,
            percentil_premium=88.0,
            spread_adjusted=-3.0,
            z_pace=0.3,
            var_cambio_5d=-0.5,
            chicago_percentile=55.0,
            chicago_is_spike=False,
            logistics_flag_active=False,
            logistics_reason=None,
        ),
        "book": None,
    },
    "logistica": {
        "nome": "🚨 Override: Logistics Crisis",
        "descricao": "Trucker strike - highest priority override",
        "inputs": MarketInputs(
            dt=date(2024, 3, 25),
            var_semanal_lineup=5.0,
            percentil_premium=70.0,
            spread_adjusted=-8.0,
            z_pace=0.8,
            var_cambio_5d=0.2,
            chicago_percentile=55.0,
            chicago_is_spike=False,
            logistics_flag_active=True,
            logistics_reason="Trucker strike - ports with queue > 20 days",
        ),
        "book": None,
    },
    "limite_book": {
        "nome": "🛑 Modulation: Book Limit",
        "descricao": "Strong market, but already at exposure limit",
        "inputs": MarketInputs(
            dt=date(2024, 6, 5),
            var_semanal_lineup=12.0,
            percentil_premium=78.0,
            spread_adjusted=-15.0,
            z_pace=1.0,
            var_cambio_5d=-1.5,
            chicago_percentile=65.0,
            chicago_is_spike=False,
            logistics_flag_active=False,
            logistics_reason=None,
        ),
        "book": BookState(
            exposicao_fisica_pct=80.0,
            limite_long_pct=80.0,
            limite_short_pct=-50.0,
            hedge_atual_pct=60.0,
            hedge_meta_pct=60.0,
        ),
    },
    "chicago_spike": {
        "nome": "⚡ Override: Speculative Chicago",
        "descricao": "8% Chicago spike without fundamentals - hedge opportunity",
        "inputs": MarketInputs(
            dt=date(2024, 7, 15),
            var_semanal_lineup=3.0,
            percentil_premium=55.0,
            spread_adjusted=2.0,
            z_pace=0.1,
            var_cambio_5d=0.3,
            chicago_percentile=78.0,
            chicago_is_spike=True,
            logistics_flag_active=False,
            logistics_reason=None,
            narrativa_confirmada=False,
        ),
        "book": None,
    },
}

st.markdown("### Select a Scenario")

cols = st.columns(4)
selected = None

for i, (key, scenario) in enumerate(SCENARIOS.items()):
    col = cols[i % 4]
    with col:
        if st.button(scenario["nome"], key=key, use_container_width=True):
            selected = key

if 'selected_scenario' not in st.session_state:
    st.session_state.selected_scenario = 'normal'

if selected:
    st.session_state.selected_scenario = selected

scenario = SCENARIOS[st.session_state.selected_scenario]

st.markdown("---")

engine = DecisionEngine(scenario["book"])
report = engine.run(scenario["inputs"])

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown(f"### {scenario['nome']}")
    st.markdown(f"*{scenario['descricao']}*")

    score = report.score_fisico
    if score >= 80:
        score_class = "score-muito-forte"
    elif score >= 65:
        score_class = "score-forte"
    elif score <= 20:
        score_class = "score-muito-fraco"
    elif score <= 35:
        score_class = "score-fraco"
    else:
        score_class = "score-neutro"

    classification_map = {
        "muito_forte": "VERY STRONG",
        "forte": "STRONG",
        "neutro": "NEUTRAL",
        "fraco": "WEAK",
        "muito_fraco": "VERY WEAK"
    }
    classification_display = classification_map.get(report.classificacao, report.classificacao.upper())

    st.markdown(f"""
    <div class="{score_class} score-display">
        {score:.0f}
        <div style="font-size: 1rem; font-weight: 400;">{classification_display}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("#### Recommendations")

    acao_fisica = report.recomendacao_fisica['acao']
    acao_map = {"aumentar_forte": "STRONG INCREASE", "aumentar": "INCREASE", "manter": "HOLD", "reduzir": "REDUCE", "reduzir_forte": "STRONG REDUCE"}
    acao_display = acao_map.get(acao_fisica, acao_fisica.upper())

    if 'aumentar' in acao_fisica:
        rec_class = "rec-aumentar"
        icon = "📈"
    elif 'reduzir' in acao_fisica:
        rec_class = "rec-reduzir"
        icon = "📉"
    else:
        rec_class = "rec-manter"
        icon = "➡️"

    intensity_map = {"forte": "Strong", "moderada": "Moderate", "neutra": "Neutral"}
    intensity_display = intensity_map.get(report.recomendacao_fisica['intensidade'], report.recomendacao_fisica['intensidade'])

    st.markdown(f"""
    <div class="rec-box {rec_class}">
        <strong>{icon} Physical:</strong> {acao_display}<br>
        <small>Intensity: {intensity_display} | Sizing: {report.recomendacao_fisica['sizing_pct']:+.0f}%</small>
    </div>
    """, unsafe_allow_html=True)

    acao_hedge = report.recomendacao_hedge['acao']
    acao_hedge_display = acao_map.get(acao_hedge, acao_hedge.upper())

    if 'aumentar' in acao_hedge:
        rec_class = "rec-aumentar"
        icon = "🛡️"
    elif 'reduzir' in acao_hedge:
        rec_class = "rec-reduzir"
        icon = "📉"
    else:
        rec_class = "rec-manter"
        icon = "➡️"

    st.markdown(f"""
    <div class="rec-box {rec_class}">
        <strong>{icon} Hedge:</strong> {acao_hedge_display}<br>
        <small>Delta: {report.recomendacao_hedge['delta_pp']:+.0f}pp vs target</small>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### Overrides")

    override_names = {
        'logistica': 'Logistics',
        'queda_conjunta': 'Joint Drop',
        'armadilha_premio': 'Premium Trap',
        'competitividade_critica': 'Critical Competitiveness',
        'chicago_especulativo': 'Speculative Chicago'
    }

    override_types = ['logistica', 'queda_conjunta', 'armadilha_premio', 'competitividade_critica', 'chicago_especulativo']
    active_overrides = report.overrides_ativos

    override_html = ""
    for ov in override_types:
        display_name = override_names.get(ov, ov.replace("_", " ").title())
        if ov in active_overrides:
            override_html += f'<span class="override-badge override-active">{display_name}</span>'
        else:
            override_html += f'<span class="override-badge override-inactive">{display_name}</span>'

    st.markdown(override_html, unsafe_allow_html=True)

    if report.override_dominante:
        dominant_display = override_names.get(report.override_dominante, report.override_dominante)
        st.warning(f"**Dominant Override:** {dominant_display}")

    if report.modulacao_aplicada:
        st.info(f"**Modulation:** {report.modulacao_razao}")


with col2:
    st.markdown("### Score Components")

    components = report.componentes

    component_names = {'lineup': 'Lineup', 'premio': 'Premium', 'competitividade': 'Competitiveness', 'demanda': 'Demand', 'cambio': 'FX Rate'}

    for name, data in components.items():
        score_val = data['score']
        if score_val >= 65:
            color = "#28a745"
        elif score_val <= 35:
            color = "#dc3545"
        else:
            color = "#ffc107"

        weights = {'lineup': 30, 'premio': 25, 'competitividade': 20, 'demanda': 15, 'cambio': 10}
        weight = weights.get(name, 0)

        display_name = component_names.get(name, name.title())

        col_a, col_b, col_c = st.columns([2, 6, 2])
        with col_a:
            st.markdown(f"**{display_name}** ({weight}%)")
        with col_b:
            st.progress(score_val / 100)
        with col_c:
            st.markdown(f"**{score_val:.0f}**")

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("### Scenario Inputs")

    inputs = scenario["inputs"]
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown(f"""
        | Indicator | Value |
        |-----------|-------|
        | Weekly Lineup Var. | {inputs.var_semanal_lineup:+.1f}% |
        | Premium Percentile | {inputs.percentil_premium:.0f} |
        | Adjusted Spread | {inputs.spread_adjusted:+.1f} USD/ton |
        """)

    with col_b:
        st.markdown(f"""
        | Indicator | Value |
        |-----------|-------|
        | Demand Z-Pace | {inputs.z_pace:+.2f} |
        | FX Var. 5d | {inputs.var_cambio_5d:+.1f}% |
        | Chicago Percentile | {inputs.chicago_percentile:.0f} |
        """)

    st.markdown("### Justification")
    st.info(report.justificativa)

    with st.expander("View Complete JSON Output"):
        st.json(report.to_dict())
