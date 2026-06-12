from datetime import date

import streamlit as st

from basismind.book import BookState
from basismind.engine import DecisionEngine, MarketInputs
from basismind.scoring import compute_scoring
from data import SCENARIO_VALUES
from ui import (
    ACTION_LABELS,
    action_card,
    contribution_waterfall,
    note,
    override_chips,
    plot,
    score_gauge,
)

st.title("Simulator")
st.caption(
    "Move the sliders and watch the engine react in real time. Start from a preset "
    "to see a known market shape, then break it."
)

PRESETS = {
    "Balanced": dict(
        var_semanal_lineup=5.0,
        percentil_premium=50.0,
        spread_adjusted=0.0,
        z_pace=0.0,
        var_cambio_5d=0.0,
        chicago_percentile=50.0,
        chicago_is_spike=False,
        logistics_flag_active=False,
    ),
} | SCENARIO_VALUES

for key, value in PRESETS["Balanced"].items():
    st.session_state.setdefault(key, value)


def _apply_preset() -> None:
    chosen = st.session_state.sim_preset
    if chosen:
        st.session_state.update(PRESETS[chosen])


st.pills(
    "Presets",
    list(PRESETS),
    label_visibility="collapsed",
    key="sim_preset",
    on_change=_apply_preset,
)

col_inputs, col_results = st.columns([1, 1.25], gap="large")

with col_inputs:
    st.markdown("##### Market signals")

    var_lineup = st.slider(
        "Line-up weekly variation (%)",
        -25.0,
        25.0,
        step=1.0,
        key="var_semanal_lineup",
        help="How fast the vessel queue is growing or shrinking vs last week. "
        "Ships waiting to load are demand you can see — below -10% it can arm "
        "the Joint Drop and Premium Trap overrides.",
    )
    percentil_premium = st.slider(
        "Premium percentile (regime-adjusted)",
        0.0,
        100.0,
        step=1.0,
        key="percentil_premium",
        help="Where today's export premium sits vs 3 years of the same regime "
        "(crop / off-season). P80 means richer than 80% of comparable days.",
    )
    spread = st.slider(
        "Adjusted FOB spread (USD/ton)",
        -30.0,
        30.0,
        step=1.0,
        key="spread_adjusted",
        help="FOB Paranaguá minus FOB US Gulf, freight-adjusted. Positive = Brazil "
        "is the expensive origin. Above +15 the Competitiveness override fires.",
    )
    z_pace = st.slider(
        "Export pace (z-score)",
        -2.0,
        2.0,
        step=0.1,
        key="z_pace",
        help="Weekly exports vs the 5-year average for the same calendar week, "
        "in standard deviations.",
    )
    var_cambio = st.slider(
        "USD/BRL 5-day variation (%)",
        -5.0,
        5.0,
        step=0.1,
        key="var_cambio_5d",
        help="Positive = weaker real. The engine treats a strengthening real as "
        "margin-supportive for new sales.",
    )
    chicago_pct = st.slider(
        "Chicago percentile (180d)",
        0.0,
        100.0,
        step=1.0,
        key="chicago_percentile",
        help="Where the CBOT front month sits vs the last 180 days. Drives the "
        "hedge recommendation: high percentile = lock prices in.",
    )

    st.markdown("##### Flags")
    f1, f2 = st.columns(2)
    chicago_spike = f1.toggle(
        "Chicago spike >5% / 5d",
        key="chicago_is_spike",
        help="A fast rally without confirmed fundamentals is treated as a hedging "
        "window, not a buying signal.",
    )
    logistics_active = f2.toggle(
        "Logistics flag",
        key="logistics_flag_active",
        help="Strike, port congestion, loading rate collapse. Highest-priority "
        "override: forces a strong reduction.",
    )

    narrativa_confirmada = False
    logistics_reason = None
    if chicago_spike:
        narrativa_confirmada = st.toggle(
            "Narrative confirmed (drought, war...)",
            help="If the move has real fundamentals behind it, the spike override "
            "stands down.",
        )
    if logistics_active:
        logistics_reason = st.text_input("Logistics reason", value="Port congestion")

    with st.expander("Book state (optional)"):
        use_book = st.toggle("Apply book limits")
        exposicao = st.slider("Current exposure (%)", -50.0, 100.0, 30.0, 5.0)
        limite_long = st.slider("Long limit (%)", 50.0, 100.0, 80.0, 5.0)
        limite_short = st.slider("Short limit (%)", -100.0, 0.0, -50.0, 5.0)
        hedge_atual = st.slider("Current hedge (%)", 0.0, 100.0, 50.0, 5.0)
        hedge_meta = st.slider("Hedge target (%)", 0.0, 100.0, 60.0, 5.0)

    book = (
        BookState(
            exposicao_fisica_pct=exposicao,
            limite_long_pct=limite_long,
            limite_short_pct=limite_short,
            hedge_atual_pct=hedge_atual,
            hedge_meta_pct=hedge_meta,
        )
        if use_book
        else None
    )

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
    logistics_reason=logistics_reason,
    narrativa_confirmada=narrativa_confirmada,
)

report = DecisionEngine(book).run(inputs)
raw = compute_scoring(
    dt=inputs.dt,
    var_semanal_lineup=inputs.var_semanal_lineup,
    percentil_premium=inputs.percentil_premium,
    spread_adjusted=inputs.spread_adjusted,
    z_pace=inputs.z_pace,
    var_cambio_5d=inputs.var_cambio_5d,
    chicago_percentile=inputs.chicago_percentile,
    chicago_is_spike=inputs.chicago_is_spike,
)

with col_results:
    plot(score_gauge(report.score_fisico, report.classificacao, height=230))

    a1, a2 = st.columns(2)
    with a1:
        action_card(
            "Physical position",
            report.recomendacao_fisica["acao"],
            f"sizing {report.recomendacao_fisica['sizing_pct']:+.0f}%",
        )
    with a2:
        action_card(
            "Chicago hedge",
            report.recomendacao_hedge["acao"],
            f"delta {report.recomendacao_hedge['delta_pp']:+.0f}pp",
        )

    raw_phys = raw.physical.recommendation.value
    raw_hedge = raw.hedge.recommendation.value
    final_phys = report.recomendacao_fisica["acao"]
    final_hedge = report.recomendacao_hedge["acao"]

    if raw_phys != final_phys or raw_hedge != final_hedge:
        reasons = []
        if report.override_dominante:
            reasons.append("an override dominated the score")
        if report.modulacao_aplicada:
            reasons.append("book limits modulated the action")
        changes = []
        if raw_phys != final_phys:
            changes.append(
                f"physical {ACTION_LABELS[raw_phys]} → {ACTION_LABELS[final_phys]}"
            )
        if raw_hedge != final_hedge:
            changes.append(
                f"hedge {ACTION_LABELS[raw_hedge]} → {ACTION_LABELS[final_hedge]}"
            )
        note(
            f"<b>The score alone would say something else:</b> {' · '.join(changes)} "
            f"— because {' and '.join(reasons)}."
        )

    st.markdown("##### Overrides")
    override_chips(report.overrides_ativos)
    if report.modulacao_aplicada:
        st.info(report.modulacao_razao, icon=":material/shield:")

    st.markdown("##### Score build-up")
    plot(contribution_waterfall(report.componentes, report.score_fisico, height=250))

    with st.expander("Justification & JSON"):
        st.markdown(f"_{report.justificativa}_")
        st.json(report.to_dict())
