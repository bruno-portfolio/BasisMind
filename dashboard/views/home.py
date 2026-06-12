import streamlit as st

from basismind.engine import DecisionEngine
from data import derive_market_inputs, load_history
from ui import (
    card,
    contribution_waterfall,
    hero,
    note,
    override_chips,
    plot,
    recommendation_cards,
    score_gauge,
)

hero(
    "Basis<span>Mind</span>",
    "A decision engine for physical grain trading. It turns scattered market signals "
    "— vessel line-ups, export premiums, FOB spreads, FX — into one auditable "
    "recommendation: what to do with your physical position and your Chicago hedge.",
    [
        "5 market signals",
        "5 override rules",
        "128 behavior tests",
        "Python 3.11",
        "MIT",
    ],
)

history = load_history()
inputs = derive_market_inputs(history)
report = DecisionEngine().run(inputs)

st.markdown("## Today's decision, live")
st.caption(
    f"Computed end-to-end right now: 3 years of synthetic market data → signal "
    f"normalization (percentiles, z-scores, freight-adjusted spreads) → scoring → "
    f"overrides → recommendation. Reference date: {report.data_referencia}."
)

col_gauge, col_actions, col_wf = st.columns([1, 1, 1.3])

with col_gauge:
    plot(score_gauge(report.score_fisico, report.classificacao))

with col_actions:
    recommendation_cards(report)
    override_chips(report.overrides_ativos)

with col_wf:
    plot(contribution_waterfall(report.componentes, report.score_fisico))

note(f"<b>Why:</b> {report.justificativa}")

st.markdown("## How it works")

c1, c2, c3, c4 = st.columns(4)
with c1:
    card(
        "step 1 — signals",
        "Read the market",
        "Five signals are normalized to a 0–100 scale: vessel line-up momentum, "
        "premium percentile vs the same crop regime, Brazil-vs-US Gulf FOB spread, "
        "export pace z-score, and USD/BRL movement.",
    )
with c2:
    card(
        "step 2 — score",
        "Weigh the evidence",
        "Signals are combined with calibrated weights (line-up 30%, premium 25%, "
        "competitiveness 20%, demand 15%, FX 10%) into a single physical score.",
    )
with c3:
    card(
        "step 3 — overrides",
        "Respect the exceptions",
        "Five rules dominate the score in situations that rarely forgive: logistics "
        "crises, joint drops, premium traps, lost competitiveness, speculative spikes.",
    )
with c4:
    card(
        "step 4 — book",
        "Stay inside limits",
        "The recommendation is modulated by your current book: exposure limits cap "
        "the sizing, and an over-hedged book blocks further hedge increases.",
    )

st.markdown("")

left, right = st.columns([1.2, 1])

with left:
    st.markdown("### What it answers")
    st.markdown("""
| Axis | Question | Answer space |
|------|----------|--------------|
| **Physical** | Accelerate sales, hold, or reduce exposure? | strong increase → strong reduce, with sizing |
| **Hedge** | Increase the Chicago hedge, hold, or reduce? | ±20pp vs the hedge target |

Every output ships with a traceable justification — which signals drove it, which
override dominated, and whether book limits modulated the final action.
""")

with right:
    st.markdown("### What it refuses to do")
    st.markdown("""
- **No price prediction** — it reads the present, it does not forecast.
- **No autopilot** — it standardizes the reading; the trader decides.
- **No geopolitics** — exogenous shocks enter via the logistics flag, not magic.
""")

st.markdown("### Where to go next")

n1, n2, n3 = st.columns(3)
with n1:
    card(
        "decide",
        "Decision Engine →",
        "Six curated scenarios — from calm markets to logistics crises — showing how "
        "the engine reasons in each one.",
    )
with n2:
    card(
        "play",
        "Simulator →",
        "Move every slider yourself and watch the score, overrides and modulation "
        "react in real time.",
    )
with n3:
    card(
        "learn",
        "Methodology →",
        "The full rulebook: glossary, component math, override conditions and the "
        "Python API.",
    )
