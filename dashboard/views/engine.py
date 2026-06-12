from datetime import date

import streamlit as st

from basismind.book import BookState
from basismind.engine import DecisionEngine, MarketInputs
from data import SCENARIO_VALUES
from ui import (
    COMPONENT_LABELS,
    COMPONENT_WEIGHTS,
    OVERRIDE_LABELS,
    contribution_waterfall,
    note,
    override_chips,
    plot,
    recommendation_cards,
    score_gauge,
)

st.title("Decision Engine")
st.caption(
    "Six curated scenarios. Pick one and follow the engine's reasoning: "
    "signals → score → overrides → book modulation → final action."
)

SCENARIOS = {
    "Balanced market": dict(
        story="Crop season underway, every signal near its comfort zone. The score "
        "lands in neutral territory and the engine holds — no signal is strong "
        "enough to justify action.",
        dt=date(2024, 5, 15),
        values=dict(
            var_semanal_lineup=5.0,
            percentil_premium=65.0,
            spread_adjusted=-5.0,
            z_pace=0.3,
            var_cambio_5d=-0.5,
            chicago_percentile=55.0,
            chicago_is_spike=False,
            logistics_flag_active=False,
        ),
        book=None,
    ),
    "Export boom": dict(
        story="Line-up surging, premium in the top quintile, Brazil priced well "
        "below the US Gulf, exports running hot. Everything points the same way — "
        "the score breaks 80 and the engine recommends a strong increase.",
        dt=date(2024, 6, 1),
        values=SCENARIO_VALUES["Export boom"],
        book=None,
    ),
    "Joint drop": dict(
        story="Line-up collapsing AND the premium already cheap. This is not a "
        "buying opportunity — it is real demand leaving the market. The Joint Drop "
        "override fires and forces a reduction regardless of the blended score.",
        dt=date(2024, 4, 20),
        values=SCENARIO_VALUES["Joint drop"],
        book=None,
    ),
    "Premium trap": dict(
        story="Premium in the 88th percentile looks like a gift — but the line-up "
        "is falling 12% a week. The price has not corrected yet; demand is already "
        "gone. The Premium Trap override sells into the strength before the "
        "correction.",
        dt=date(2024, 5, 10),
        values=SCENARIO_VALUES["Premium trap"],
        book=None,
    ),
    "Logistics crisis": dict(
        story="A trucker strike with 20-day port queues. Market signals still look "
        "healthy — which is exactly why this is the highest-priority override: the "
        "bottleneck will be priced in before it shows up in the data.",
        dt=date(2024, 3, 25),
        values=SCENARIO_VALUES["Logistics crisis"],
        reason="Trucker strike — ports with queue > 20 days",
        book=None,
    ),
    "At the book limit": dict(
        story="A strong market asking for more exposure — but the book is already "
        "at its 80% long limit. The score says increase; the book says no. "
        "Modulation caps the action at HOLD and says so explicitly.",
        dt=date(2024, 6, 5),
        values=dict(
            var_semanal_lineup=12.0,
            percentil_premium=78.0,
            spread_adjusted=-15.0,
            z_pace=1.0,
            var_cambio_5d=-1.5,
            chicago_percentile=65.0,
            chicago_is_spike=False,
            logistics_flag_active=False,
        ),
        book=BookState(
            exposicao_fisica_pct=80.0,
            limite_long_pct=80.0,
            limite_short_pct=-50.0,
            hedge_atual_pct=60.0,
            hedge_meta_pct=60.0,
        ),
    ),
    "Chicago spike": dict(
        story="Chicago jumped 8% in five days with no confirmed fundamental story. "
        "Chasing it is negative asymmetry — so the engine holds the physical and "
        "uses the spike as a hedging window instead (+20pp).",
        dt=date(2024, 7, 15),
        values=SCENARIO_VALUES["Chicago spike"],
        book=None,
    ),
}

choice = (
    st.pills(
        "Scenario",
        list(SCENARIOS),
        default="Balanced market",
        label_visibility="collapsed",
    )
    or "Balanced market"
)
scenario = SCENARIOS[choice]

inputs = MarketInputs(
    dt=scenario["dt"],
    logistics_reason=scenario.get("reason"),
    **scenario["values"],
)
report = DecisionEngine(scenario["book"]).run(inputs)

note(f"<b>{choice}.</b> {scenario['story']}")
st.markdown("")

col_left, col_right = st.columns([1, 1.45])

with col_left:
    plot(score_gauge(report.score_fisico, report.classificacao))
    recommendation_cards(report)

with col_right:
    st.markdown("##### Score build-up")
    plot(contribution_waterfall(report.componentes, report.score_fisico, height=270))

    st.markdown("##### Overrides")
    override_chips(report.overrides_ativos)
    if report.override_dominante:
        st.warning(
            f"**{OVERRIDE_LABELS[report.override_dominante]}** dominated the score — "
            "the recommendation above comes from the override rule, not the blend.",
            icon=":material/priority_high:",
        )
    if report.modulacao_aplicada:
        st.info(
            f"**Book modulation:** {report.modulacao_razao}", icon=":material/shield:"
        )

st.markdown("##### The signals behind it")

signal_rows = [
    ("Line-up", "lineup", f"{inputs.var_semanal_lineup:+.1f}%", "weekly variation"),
    ("Premium", "premio", f"P{inputs.percentil_premium:.0f}", "percentile in regime"),
    (
        "Spread",
        "competitividade",
        f"{inputs.spread_adjusted:+.1f}",
        "USD/ton vs US Gulf",
    ),
    ("Demand", "demanda", f"{inputs.z_pace:+.2f}σ", "export pace z-score"),
    ("FX 5d", "cambio", f"{inputs.var_cambio_5d:+.1f}%", "USD/BRL variation"),
]
for col, (name, key, value, desc) in zip(st.columns(5), signal_rows):
    score = report.componentes[key]["score"]
    col.metric(
        f"{name} · {COMPONENT_WEIGHTS[key]}%",
        value,
        f"score {score:.0f}",
        delta_color="off",
        help=f"{COMPONENT_LABELS[key]} — {desc}",
    )

st.markdown("")
note(f"<b>Justification:</b> {report.justificativa}")

with st.expander("Full JSON report"):
    st.json(report.to_dict())
