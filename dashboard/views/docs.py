from calendar import month_abbr

import streamlit as st

from basismind.competitiveness import FREIGHT_DIFFERENTIAL_MONTHLY
from ui import note

FREIGHT_TABLE = (
    "| "
    + " | ".join(month_abbr[m] for m in range(1, 13))
    + " |\n"
    + "|"
    + "----:|" * 12
    + "\n"
    + "| "
    + " | ".join(
        (
            f"{FREIGHT_DIFFERENTIAL_MONTHLY[m]:+.0f}"
            if FREIGHT_DIFFERENTIAL_MONTHLY[m]
            else "0"
        )
        for m in range(1, 13)
    )
    + " |"
)

st.title("Methodology")
st.caption(
    "The full rulebook: what each term means, how every component is computed, "
    "when overrides take over, and how to use the engine from Python."
)

tab_glossary, tab_components, tab_overrides, tab_architecture, tab_api = st.tabs(
    ["Glossary", "Components", "Overrides", "Architecture", "Python API"]
)

with tab_glossary:
    note(
        "Physical grain trading has its own vocabulary. Every screen in this app "
        "uses these terms — five minutes here makes the rest self-explanatory."
    )
    st.markdown("""
| Term | Meaning |
|------|---------|
| **Basis / Premium** | What buyers pay **over the Chicago futures price** for physical beans at a given port. Chicago sets the global reference; the premium prices local supply, demand and logistics. BasisMind's name comes from here. |
| **FOB** | *Free On Board* — the price of grain loaded on the vessel at the origin port, freight not included. Comparing FOB Paranaguá vs FOB US Gulf compares origins like-for-like. |
| **FOB spread** | FOB Paranaguá − FOB US Gulf, adjusted for the seasonal freight differential. Positive spread = Brazil is the expensive origin and buyers can switch. |
| **Line-up** | The queue of vessels scheduled to load at port in the next 2–6 weeks. It is demand you can physically count — and it moves before prices do. |
| **Net line-up** | Gross line-up minus cancellations and long postponements. A growing gross with surging cancellations is weakness, not strength. |
| **Crop regime** | Brazil ships most soybeans Mar–Jul (*safra*). Premiums behave so differently across regimes that comparing a March premium with an October one is meaningless — hence percentile-by-regime. |
| **Percentile** | Where today's value ranks vs 3 years of the same regime. P82 = richer than 82% of comparable days. Robust to outliers, assumes no distribution. |
| **Z-score (pace)** | Weekly exports vs the 5-year average for that same calendar week, in standard deviations. +1.5σ = demand running very hot. |
| **Hedge** | A short position in Chicago futures protecting physical inventory from board-price moves. The engine recommends a hedge ratio relative to a target. |
| **Book** | Your current position: physical exposure vs long/short limits, current hedge vs target. The book never changes what the market says — it caps what you can do about it. |
| **Sizing** | The suggested change in physical position, as % of capacity. Bounded ±25%, then capped by available book headroom. |
| **Override** | A rule that replaces the score's recommendation when a pattern that rarely forgives shows up. Five exist; the most conservative one wins. |
| **Modulation** | The book stepping in: at the long limit, INCREASE becomes HOLD; over-hedged, hedge increases are blocked. Always reported explicitly. |
""")

with tab_components:
    note(
        "Each component is normalized to 0–100 with a linear map between calibrated "
        "bounds, then blended with fixed weights. All bounds live in "
        "<code>config.py</code> — one constant per knob, no magic numbers in code."
    )
    st.markdown(f"""
### Line-up — 30%

Weekly % variation of the net line-up. `linear_map(var, -15%, +15%) → 0–100`.
The heaviest weight because counted ships are the hardest demand signal available.

### Premium — 25%

Percentile of today's premium vs 3 years of the **same crop regime**.
The percentile *is* the score.
Why not z-scores? Premium distributions have fat tails and skew — percentiles
don't care.

### Competitiveness — 20%

Adjusted FOB spread = (FOB Paranaguá − FOB US Gulf) + monthly freight
differential. `linear_map(spread, +20, -20) → 0–100` — **inverse**: cheap
Brazil scores high.

When the observed freight deviates more than 2σ from its own history, the
spread is treated as distorted and this component's weight is halved
(renormalized across the blend) until freight normalizes.

Freight differential by month (USD/ton):

{FREIGHT_TABLE}

### Demand — 15%

Z-score of weekly exports vs the 5-year same-week average.
`linear_map(z, -1.5σ, +1.5σ) → 0–100`.

### FX — 10%

USD/BRL variation over 5 days. `linear_map(var, +3%, -3%) → 0–100` —
**inverse**: a strengthening real scores high. The logic is supply retention:
a strong real slows farmer selling, which keeps premiums supported. Smallest
weight — FX shapes flow at the margin, it doesn't create demand.

### Missing data

Any `None` input scores a neutral 50. The engine degrades gracefully instead
of refusing to run — and the justification still names which signals drove
the decision.
""")

with tab_overrides:
    note(
        "Scores average evidence; some situations must not be averaged. Each "
        "override encodes a pattern that experienced desks treat as non-negotiable. "
        "When several fire, the lowest priority number — the most conservative — "
        "wins, and the report names it."
    )
    st.markdown("""
### 1 · Logistics — `STRONG REDUCE (−30%)`

**Fires when:** the logistics flag is active — vessel waiting time above 15
days for 2+ consecutive weeks, loading rate below 70%, or a manual event
(strike, interdiction).

**Logic:** a bottleneck gets priced into premiums *before* it appears in any
other signal. Highest priority of all: it overrides even a booming market.

### 2 · Joint Drop — `REDUCE (−20%)`

**Fires when:** line-up < −10% weekly **and** premium below P40.

**Logic:** falling demand *and* a cheap premium is not a discount — it is the
market leaving. Buying "cheap" here is catching the knife.

### 3 · Premium Trap — `STRONG REDUCE (−25%)`

**Fires when:** premium above P80 **and** line-up < −10% weekly.

**Logic:** the price hasn't corrected yet but demand is already gone. The
rich premium is a window to sell into, not a reason to hold.

### 4 · Critical Competitiveness — `REDUCE (−15%)`

**Fires when:** adjusted spread > +15 USD/ton.

**Logic:** buyers have a cheaper origin one click away. Volume migrates to
the US Gulf until Brazil reprices.

### 5 · Chicago Spike — `HOLD physical · hedge +20pp`

**Fires when:** Chicago rose more than 5% in 5 days **without** a confirmed
fundamental narrative (drought, war, policy).

**Logic:** chasing a speculative rally is negative asymmetry. Don't buy the
move — use it as a hedging window.
""")

with tab_architecture:
    note(
        "A pure-Python decision core with zero I/O in the decision path — every "
        "function from signal to recommendation is deterministic and unit-tested "
        "(128 behavior tests). Data ingestion, validation and persistence live in "
        "separate modules."
    )
    st.markdown("""
### Package layout

```
src/basismind/
├── config.py           every threshold and weight, one place
├── scoring.py          signal normalization + weighted blend
├── overrides.py        the five rules + priority resolution
├── book.py             exposure limits, hedge target, sizing caps
├── engine.py           orchestration → DecisionReport (JSON-ready)
├── premium.py          regime detection + percentile ranking
├── lineup.py           net line-up, cancellation rate, trends
├── competitiveness.py  FOB spread + freight adjustment
├── auxiliaries.py      FX, demand pace, logistics flag, Chicago
├── database.py         SQLite persistence + quality log
├── validators.py       range/consistency/anomaly gates
├── pipeline.py         pluggable ingestion (CSV, manual, ...)
├── alerts.py           console / file / e-mail alerting
└── mock_generator.py   3y synthetic market data (this app's source)
```

### Decision flow

```
signals ──► scoring ──► overrides ──► book modulation ──► DecisionReport
            (blend)     (exceptions)   (your limits)        (traceable)
```

Every stage only narrows the previous one — and every narrowing is named in
the final justification, so a recommendation can always be explained
backwards.
""")

with tab_api:
    note(
        "The dashboard is one consumer. The same engine is importable, "
        "deterministic, and returns a JSON-serializable report — drop it in a "
        "notebook, a cron job, or behind an API."
    )
    st.markdown("""
```python
from datetime import date
from basismind import DecisionEngine, MarketInputs, BookState

book = BookState(
    exposicao_fisica_pct=30.0,
    limite_long_pct=80.0,
    limite_short_pct=-50.0,
    hedge_atual_pct=45.0,
    hedge_meta_pct=60.0,
)
engine = DecisionEngine(book)

inputs = MarketInputs(
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
)

report = engine.run(inputs)
print(report.score_fisico)                  # 91.3
print(report.recomendacao_fisica["acao"])   # aumentar_forte
print(report.to_json())
```

Lower-level pieces are importable on their own:

```python
from basismind.scoring import score_lineup, compute_scoring
from basismind.overrides import check_armadilha_premio
from basismind.premium import calculate_percentile, get_regime
```

Output of `report.to_json()` for the inputs above:

```json
{
  "data_referencia": "2024-06-01",
  "score_fisico": 91.3,
  "classificacao": "muito_forte",
  "recomendacao_fisica": {
    "acao": "aumentar_forte",
    "intensidade": "forte",
    "sizing_pct": 25.0
  },
  "recomendacao_hedge": {
    "acao": "aumentar",
    "intensidade": "moderada",
    "delta_pp": 10.0
  },
  "componentes": {
    "lineup": {"score": 100.0, "var_semanal": 15.0},
    "premio": {"score": 82.0, "percentil": 82.0},
    "competitividade": {"score": 95.0, "spread": -18.0},
    "demanda": {"score": 90.0, "z_pace": 1.2},
    "cambio": {"score": 83.3, "var_5d": -2.0}
  },
  "overrides_ativos": [],
  "override_dominante": null,
  "modulacao_aplicada": false,
  "modulacao_razao": null,
  "justificativa": "Fisico muito_forte (score 91) | Drivers: lineup forte, competitividade forte | Recomendacao: aumentar_forte (fisica), aumentar (hedge)"
}
```
""")
