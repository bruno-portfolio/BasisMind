import streamlit as st
import sys
from pathlib import Path
from datetime import date

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "data"))

from engine import DecisionEngine, MarketInputs
from book import BookState

st.set_page_config(page_title="Simulator | BasisMind", page_icon="🔄", layout="wide")

st.title("🔄 Scenario Simulator")
st.markdown("Adjust the parameters and see how the engine responds in real-time.")

col_inputs, col_results = st.columns([1, 1])

with col_inputs:
    st.markdown("### Market Parameters")

    tab1, tab2, tab3 = st.tabs(["Main", "Auxiliary", "Book"])

    with tab1:
        st.markdown("#### Line-up")
        var_lineup = st.slider(
            "Weekly Variation (%)",
            min_value=-25.0,
            max_value=25.0,
            value=5.0,
            step=1.0,
            help="Percentage variation of net line-up vs previous week",
        )

        st.markdown("#### Premium")
        percentil_premium = st.slider(
            "Premium Percentile",
            min_value=0.0,
            max_value=100.0,
            value=50.0,
            step=5.0,
            help="Current premium position vs historical for same regime",
        )

        st.markdown("#### Competitiveness")
        spread = st.slider(
            "Adjusted Spread (USD/ton)",
            min_value=-30.0,
            max_value=30.0,
            value=0.0,
            step=1.0,
            help="FOB Paranagua - FOB US Gulf (freight adjusted). Positive = Brazil more expensive",
        )

    with tab2:
        st.markdown("#### Demand")
        z_pace = st.slider(
            "Pace Z-Score",
            min_value=-2.0,
            max_value=2.0,
            value=0.0,
            step=0.1,
            help="Export pace vs 5-year average for same week",
        )

        st.markdown("#### FX Rate")
        var_cambio = st.slider(
            "USD/BRL Var. 5d (%)",
            min_value=-5.0,
            max_value=5.0,
            value=0.0,
            step=0.1,
            help="Dollar variation. Positive = weaker real",
        )

        st.markdown("#### Chicago")
        chicago_pct = st.slider(
            "Chicago Percentile",
            min_value=0.0,
            max_value=100.0,
            value=50.0,
            step=5.0,
            help="Chicago position vs 180-day history",
        )

        chicago_spike = st.checkbox(
            "Speculative Spike (>5% in 5d)",
            value=False,
            help="Check if Chicago rose more than 5% in 5 days",
        )

        st.markdown("#### Logistics")
        logistics_active = st.checkbox(
            "Logistics Flag Active",
            value=False,
            help="Activate in case of strike, port congestion, etc.",
        )

        logistics_reason = None
        if logistics_active:
            logistics_reason = st.text_input(
                "Reason",
                value="Port congestion",
                help="Describe the logistics restriction reason",
            )

        narrativa_confirmada = False
        if chicago_spike:
            narrativa_confirmada = st.checkbox(
                "Confirmed Narrative",
                value=False,
                help="Check if the movement has fundamentals (drought, war, etc.)",
            )

    with tab3:
        st.markdown("#### Book State")

        use_book = st.checkbox("Apply book state", value=False)

        if use_book:
            exposicao = st.slider(
                "Current Exposure (%)",
                min_value=-50.0,
                max_value=100.0,
                value=30.0,
                step=5.0,
            )

            limite_long = st.slider(
                "Long Limit (%)",
                min_value=50.0,
                max_value=100.0,
                value=80.0,
                step=5.0,
            )

            limite_short = st.slider(
                "Short Limit (%)",
                min_value=-100.0,
                max_value=0.0,
                value=-50.0,
                step=5.0,
            )

            hedge_atual = st.slider(
                "Current Hedge (%)",
                min_value=0.0,
                max_value=100.0,
                value=50.0,
                step=5.0,
            )

            hedge_meta = st.slider(
                "Hedge Target (%)",
                min_value=0.0,
                max_value=100.0,
                value=60.0,
                step=5.0,
            )

            book = BookState(
                exposicao_fisica_pct=exposicao,
                limite_long_pct=limite_long,
                limite_short_pct=limite_short,
                hedge_atual_pct=hedge_atual,
                hedge_meta_pct=hedge_meta,
            )
        else:
            book = None


inputs = MarketInputs(
    dt=date.today(),
    var_semanal_lineup=var_lineup,
    percentil_premium=percentil_premium,
    spread_adjusted=spread,
    z_pace=z_pace,
    var_cambio_5d=var_cambio,
    chicago_percentile=chicago_pct,
    chicago_is_spike=chicago_spike,
    logistics_flag_active=logistics_active,
    logistics_reason=logistics_reason if logistics_active else None,
    narrativa_confirmada=narrativa_confirmada if chicago_spike else False,
)

engine = DecisionEngine(book)
report = engine.run(inputs)

with col_results:
    st.markdown("### Engine Result")

    score = report.score_fisico
    if score >= 80:
        color = "white"
        bg = "#28a745"
    elif score >= 65:
        color = "white"
        bg = "#28a745"
    elif score <= 20:
        color = "white"
        bg = "#dc3545"
    elif score <= 35:
        color = "white"
        bg = "#dc3545"
    else:
        color = "white"
        bg = "#fd7e14"

    classification_map = {
        "muito_forte": "VERY STRONG",
        "forte": "STRONG",
        "neutro": "NEUTRAL",
        "fraco": "WEAK",
        "muito_fraco": "VERY WEAK",
    }
    classification_display = classification_map.get(
        report.classificacao, report.classificacao.upper()
    )

    st.markdown(
        f"""
    <div style="background: {bg}; padding: 2rem; border-radius: 16px; text-align: center; margin-bottom: 1rem;">
        <div style="font-size: 4rem; font-weight: 700; color: {color};">{score:.0f}</div>
        <div style="font-size: 1.2rem; color: {color}; text-transform: uppercase;">{classification_display}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns(2)

    acao_map = {
        "aumentar_forte": "STRONG INCREASE",
        "aumentar": "INCREASE",
        "manter": "HOLD",
        "reduzir": "REDUCE",
        "reduzir_forte": "STRONG REDUCE",
    }

    with col_a:
        acao = report.recomendacao_fisica["acao"]
        acao_display = acao_map.get(acao, acao.upper())
        if "aumentar" in acao:
            st.success(f"**PHYSICAL:** {acao_display}")
        elif "reduzir" in acao:
            st.error(f"**PHYSICAL:** {acao_display}")
        else:
            st.warning(f"**PHYSICAL:** {acao_display}")
        st.caption(f"Sizing: {report.recomendacao_fisica['sizing_pct']:+.0f}%")

    with col_b:
        acao = report.recomendacao_hedge["acao"]
        acao_display = acao_map.get(acao, acao.upper())
        if "aumentar" in acao:
            st.success(f"**HEDGE:** {acao_display}")
        elif "reduzir" in acao:
            st.error(f"**HEDGE:** {acao_display}")
        else:
            st.warning(f"**HEDGE:** {acao_display}")
        st.caption(f"Delta: {report.recomendacao_hedge['delta_pp']:+.0f}pp")

    override_names = {
        "logistica": "Logistics",
        "queda_conjunta": "Joint Drop",
        "armadilha_premio": "Premium Trap",
        "competitividade_critica": "Critical Competitiveness",
        "chicago_especulativo": "Speculative Chicago",
    }

    if report.overrides_ativos:
        st.markdown("---")
        st.markdown("### Active Overrides")
        for ov in report.overrides_ativos:
            display_name = override_names.get(ov, ov.upper().replace("_", " "))
            st.error(f"**{display_name}**")
        if report.override_dominante:
            dominant_display = override_names.get(
                report.override_dominante, report.override_dominante
            )
            st.caption(f"Dominant override: {dominant_display}")

    if report.modulacao_aplicada:
        st.markdown("---")
        st.markdown("### Modulation Applied")
        st.info(report.modulacao_razao)

    st.markdown("---")
    st.markdown("### Components Breakdown")

    component_names = {
        "lineup": "Lineup",
        "premio": "Premium",
        "competitividade": "Competitiveness",
        "demanda": "Demand",
        "cambio": "FX Rate",
    }

    for name, data in report.componentes.items():
        score_val = data["score"]
        weights = {
            "lineup": 30,
            "premio": 25,
            "competitividade": 20,
            "demanda": 15,
            "cambio": 10,
        }
        weight = weights.get(name, 0)
        contribution = score_val * weight / 100

        display_name = component_names.get(name, name.title())

        col1, col2, col3 = st.columns([3, 5, 2])
        with col1:
            st.markdown(f"**{display_name}** ({weight}%)")
        with col2:
            st.progress(score_val / 100)
        with col3:
            st.markdown(f"{score_val:.0f} → {contribution:.1f}")

    st.caption("Individual score → Contribution to final score")

    st.markdown("---")
    st.markdown("### Justification")
    st.info(report.justificativa)

    with st.expander("View Complete JSON"):
        st.json(report.to_dict())
